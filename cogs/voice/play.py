import asyncio
import logging
import shlex
from pathlib import Path
from typing import Any, TypeAlias

import discord
import yt_dlp
from discord.ext import commands

import utils


SONG_REQUESTS_CHANNEL = "song-requests"
MAX_QUEUE_ITEMS_IN_EMBED = 10
VOICE_EMPTY_CHECK_INTERVAL_SECONDS = 5

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

YTDL_OPTIONS = {
    "format": "bestaudio/best[ext=m4a]/best",
    "noplaylist": True,
    "default_search": "ytsearch5",
    "quiet": True,
    "ignoreerrors": True,
    "remote_components": ["ejs:github"],
    # Deno JS runtime
    "extractor_args": {
        "youtube": {
            "player_skip": [],
        },
        "generic": {
            "impersonate": "chrome",
        },
    },
    "deno_path": "/usr/bin/deno",
}

SongInfo: TypeAlias = dict[str, Any]
QueuedSong: TypeAlias = dict[str, Any]


class MusicControls(discord.ui.View):
    """
    Music controls displayed underneath the currently playing song embed.
    """

    def __init__(self, bot: commands.Bot, player: "MusicPlayer") -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.player = player
        self.guild = player.guild
        self.logger = logging.getLogger(self.__class__.__name__)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self._is_user_in_player_channel(interaction):
            await interaction.response.send_message(
                "YOU MUST BE IN THE SAME VOICE CHANNEL",
                ephemeral=True,
            )
            return False

        return True

    def _is_user_in_player_channel(self, interaction: discord.Interaction) -> bool:
        return (
            bool(interaction.user.voice)
            and bool(self.player.voice_client)
            and interaction.user.voice.channel == self.player.voice_client.channel
        )

    async def _defer_interaction(
        self,
        interaction: discord.Interaction,
        action_name: str,
    ) -> None:
        try:
            await interaction.response.defer()
        except discord.HTTPException:
            self.logger.exception(
                "Failed to defer %s interaction in %s",
                action_name,
                self.guild.name,
            )
        except Exception:
            self.logger.exception("Unexpected error in %s interaction", action_name)

    @discord.ui.button(label="⏭ SKIP", style=discord.ButtonStyle.primary)
    async def skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.player.voice_client:
            self.player.voice_client.stop()

        await self._defer_interaction(interaction, "skip")

    @discord.ui.button(label="▶ PLAY", style=discord.ButtonStyle.success)
    async def play_pause(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.player.voice_client and self.player.voice_client.is_paused():
            self.player.voice_client.resume()

        await self._defer_interaction(interaction, "play")

    @discord.ui.button(label="⏸ PAUSE", style=discord.ButtonStyle.secondary)
    async def pause(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.player.voice_client and self.player.voice_client.is_playing():
            self.player.voice_client.pause()

        await self._defer_interaction(interaction, "pause")

    @discord.ui.button(label="⏹ STOP", style=discord.ButtonStyle.danger)
    async def stop(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.player.clear_queue()

        if self.player.voice_client:
            self.player.voice_client.stop()

        await self._defer_interaction(interaction, "stop")


class MusicPlayer:
    """
    Server-specific music player with an independent voice client and song queue.
    """

    def __init__(self, bot: commands.Bot, guild: discord.Guild) -> None:
        self.bot = bot
        self.guild = guild
        self.logger = logging.getLogger(self.__class__.__name__)

        self.queue: asyncio.Queue[QueuedSong] = asyncio.Queue()
        self.current: QueuedSong | None = None
        self.voice_client: discord.VoiceClient | None = None
        self.play_next_event = asyncio.Event()

        self.loop_task = bot.loop.create_task(self._player_loop())

    def clear_queue(self) -> None:
        self.queue = asyncio.Queue()

    @staticmethod
    def _create_now_playing_embed(
        ctx: commands.Context, song_info: SongInfo
    ) -> discord.Embed:
        duration = song_info.get("duration", 0)
        minutes, seconds = divmod(duration, 60)

        embed = discord.Embed(
            title=f"NOW PLAYING: {song_info.get('title', 'Unknown Title')}",
            url=song_info.get("webpage_url", "Unknown URL"),
            description=f"By **{song_info.get('uploader', 'Unknown User')}**",
            colour=utils.REDDIT_RED,
        )

        embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}")
        embed.add_field(name="Views", value=f"{song_info.get('view_count', 0):,}")

        if song_info.get("thumbnail"):
            embed.set_thumbnail(url=song_info["thumbnail"])

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        return embed

    async def _player_loop(self) -> None:
        while True:
            self.current = await self.queue.get()

            try:
                await self._start_current_song()
            except Exception:
                self.logger.exception("Unexpected error in music player loop")

            await self._disconnect_if_queue_is_empty()

    async def _start_current_song(self) -> None:
        if not self.current:
            return

        ctx = self.current["ctx"]
        song_info = self.current["info"]

        try:
            await self._join_author_voice_channel(ctx)
            self._play_audio(song_info)
            await self._send_now_playing_message(ctx, song_info)
            await self._wait_until_song_finishes_or_channel_empties()
        except Exception:
            await self._reply_playback_error(ctx)
            self.logger.exception("Unexpected error starting next song")

    def _play_audio(self, song_info: SongInfo) -> None:
        ffmpeg_options = {**FFMPEG_OPTIONS}
        http_headers = song_info.get("http_headers", {})

        if http_headers:
            headers = "\r\n".join(
                f"{name}: {value}" for name, value in http_headers.items()
            )
            ffmpeg_options["before_options"] = (
                f"{ffmpeg_options['before_options']} -headers {shlex.quote(headers)}"
            )

        source = discord.FFmpegPCMAudio(song_info["url"], **ffmpeg_options)

        self.play_next_event.clear()
        self.voice_client.play(
            source,
            after=lambda error: self.bot.loop.call_soon_threadsafe(
                self.play_next_event.set
            ),
        )

    async def _send_now_playing_message(
        self,
        ctx: commands.Context,
        song_info: SongInfo,
    ) -> None:
        embed = self._create_now_playing_embed(ctx, song_info)
        view = MusicControls(self.bot, self)

        try:
            await ctx.reply(embed=embed, view=view)
        except discord.HTTPException:
            self.logger.exception(
                "Failed to send now playing embed for %s in %s",
                song_info.get("title"),
                ctx.guild.name,
            )

    async def _wait_until_song_finishes_or_channel_empties(self) -> None:
        while self.voice_client and self.voice_client.is_playing():
            if not self._has_listeners():
                self.logger.info("NO ONE LEFT IN VC. STOPPING PLAYBACK")
                self.voice_client.stop()
                break

            await asyncio.sleep(VOICE_EMPTY_CHECK_INTERVAL_SECONDS)

        await self.play_next_event.wait()
        self.play_next_event.clear()

    def _has_listeners(self) -> bool:
        if not self.voice_client or not self.voice_client.channel:
            return False

        return any(not member.bot for member in self.voice_client.channel.members)

    async def _reply_playback_error(self, ctx: commands.Context) -> None:
        try:
            await ctx.reply("ERROR PLAYING SONG")
        except discord.HTTPException:
            self.logger.exception("Failed to send error reply during song playback")

    async def _disconnect_if_queue_is_empty(self) -> None:
        if self.queue.empty() and self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None

    async def _join_author_voice_channel(self, ctx: commands.Context) -> None:
        channel = ctx.author.voice.channel

        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel != channel:
                await self.voice_client.move_to(channel)
            return

        self.voice_client = await channel.connect()


class Play(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.players: dict[int, MusicPlayer] = {}

    def _get_music_player(self, guild: discord.Guild) -> MusicPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = MusicPlayer(self.bot, guild)

        return self.players[guild.id]

    async def _search_youtube(self, query: str) -> SongInfo | None:
        def _is_url(query: str) -> bool:
            return query.startswith("http://") or query.startswith("https://")

        cookie_path = Path("cookies.txt").resolve()
        ytdl_options = {
            **YTDL_OPTIONS,
            "logger": self.logger,
            "progress_hooks": [lambda data: self.logger.debug(data)],
        }

        if cookie_path.exists():
            self.logger.debug("FOUND COOKIES: %s", cookie_path)
            ytdl_options["cookies"] = str(cookie_path)

        loop = asyncio.get_running_loop()

        def extract_info() -> SongInfo | None:
            with yt_dlp.YoutubeDL(ytdl_options) as ytdl:
                if _is_url(query):
                    return ytdl.extract_info(query, download=False)
                else:
                    return ytdl.extract_info(f"ytsearch5:{query}", download=False)

        try:
            search_result = await loop.run_in_executor(None, extract_info)
            return self._select_playable_entry(search_result, query)
        except Exception:
            self.logger.exception("YouTube search failed for query %s", query)
            return None

    def _select_playable_entry(
        self,
        search_result: SongInfo | None,
        query: str,
    ) -> SongInfo | None:
        if not search_result:
            self.logger.warning("YT search returned no results for query: %s", query)
            return None

        if "entries" in search_result:
            for entry in search_result["entries"]:
                if self._is_playable_entry(entry):
                    return entry

            self.logger.warning("No valid videos found for query: %s", query)
            return None

        if self._is_playable_entry(search_result):
            self.logger.info(
                "YT video found: title=%s url=%s",
                search_result.get("title"),
                search_result.get("webpage_url"),
            )
            return search_result

        self.logger.warning("No valid fields in info: %s", search_result)
        return None

    @staticmethod
    def _is_playable_entry(entry: SongInfo | None) -> bool:
        return bool(entry and entry.get("webpage_url") and entry.get("url"))

    @staticmethod
    def _is_song_request_channel(ctx: commands.Context) -> bool:
        return ctx.channel.name == SONG_REQUESTS_CHANNEL

    @staticmethod
    def _is_author_in_voice_channel(ctx: commands.Context) -> bool:
        return bool(ctx.author.voice and ctx.author.voice.channel)

    @staticmethod
    def _is_author_in_player_channel(
        ctx: commands.Context,
        player: MusicPlayer,
    ) -> bool:
        return (
            bool(ctx.author.voice)
            and bool(player.voice_client)
            and ctx.author.voice.channel == player.voice_client.channel
        )

    @commands.command(name="play", aliases=["music", "song", "listen"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """
        Play a YouTube video in a voice channel.

        You must be in a voice channel.
        """
        if not self._is_song_request_channel(ctx):
            return

        try:
            if not self._is_author_in_voice_channel(ctx):
                await ctx.reply("YOU ARE NOT IN A VOICE CHANNEL")
                return

            if not query:
                await ctx.reply("PLEASE PROVIDE A SEARCH QUERY")
                return

            song_info = await self._search_youtube(query)
            if not song_info:
                await ctx.reply("COULD NOT FIND A RELEVANT VIDEO")
                return

            player = self._get_music_player(ctx.guild)
            await player.queue.put({"ctx": ctx, "info": song_info})

            await ctx.reply(f"QUEUED: [{song_info['title']}]")
        except discord.HTTPException:
            self.logger.exception(
                "Failed to reply in play command for %s", ctx.author.name
            )
        except Exception:
            self.logger.exception(
                "Unexpected error in play command for query: %s", query
            )

    @commands.command(name="skip", aliases=["next", "fastforward"])
    async def skip(self, ctx: commands.Context) -> None:
        """
        Skip the currently playing song.

        You must be in the same voice channel as the bot.
        """
        if not self._is_song_request_channel(ctx):
            return

        try:
            player = self._get_music_player(ctx.guild)

            if not player.voice_client or not player.voice_client.is_connected():
                await ctx.reply("NOTHING IS PLAYING")
                return

            if not self._is_author_in_player_channel(ctx, player):
                await ctx.reply("YOU MUST BE IN THE SAME VOICE CHANNEL TO SKIP")
                return

            player.voice_client.stop()
            await ctx.reply("SKIPPED")
        except discord.HTTPException:
            self.logger.exception(
                "Failed to reply in skip command for %s", ctx.author.name
            )
        except Exception:
            self.logger.exception(
                "Unexpected error in skip command for %s", ctx.author.name
            )

    @commands.command(name="queue", aliases=["playlist", "upnext"])
    async def queue(self, ctx: commands.Context) -> None:
        """
        Show the song queue.
        """
        if not self._is_song_request_channel(ctx):
            return

        try:
            player = self._get_music_player(ctx.guild)

            if player.current is None and player.queue.empty():
                await ctx.reply("QUEUE IS EMPTY")
                return

            await ctx.reply(embed=self._create_queue_embed(player))
        except discord.HTTPException:
            self.logger.exception("Failed to send queue embed to %s", ctx.author.name)
        except Exception:
            self.logger.exception(
                "Unexpected error in queue command for %s", ctx.author.name
            )

    def _create_queue_embed(self, player: MusicPlayer) -> discord.Embed:
        embed = discord.Embed(title="QUEUE", color=utils.REDDIT_RED)

        if player.current:
            current_info = player.current["info"]
            embed.add_field(
                name="NOW PLAYING",
                value=f"[{current_info.get('title')}]({current_info.get('webpage_url')})",
                inline=False,
            )

        upcoming_songs = list(player.queue._queue)
        embed.add_field(
            name="UP NEXT",
            value=self._format_upcoming_songs(upcoming_songs),
            inline=False,
        )

        return embed

    @staticmethod
    def _format_upcoming_songs(upcoming_songs: list[QueuedSong]) -> str:
        if not upcoming_songs:
            return "NOTHING ELSE IN QUEUE"

        queue_lines = []
        for index, song in enumerate(
            upcoming_songs[:MAX_QUEUE_ITEMS_IN_EMBED], start=1
        ):
            song_info = song["info"]
            queue_lines.append(
                f"**{index}.** [{song_info.get('title')}]({song_info.get('webpage_url')})"
            )

        if len(upcoming_songs) > MAX_QUEUE_ITEMS_IN_EMBED:
            remaining_count = len(upcoming_songs) - MAX_QUEUE_ITEMS_IN_EMBED
            queue_lines.append(f"\n...and {remaining_count} more")

        return "\n".join(queue_lines)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Play(bot))
