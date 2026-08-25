import asyncio
import datetime
import json
import logging
import random

import discord
from discord.ext import commands

from utils import REDDIT_RED, karma_lock, karmic_dict


reaction_dict = {
    "reddit_upvote": 1,
    "Upvote": 1,
    "reddit_downvote": -1,
    "Downvote": -1,
    "half_upvote": 0.5,
    "quarter_upvote": 0.5,
    "half_downvote": -0.5,
    "quarter_downvote": -0.5,
    "reddit_gold": 0,
    "reddit_platinum": 0,
    "reddit_silver": 0,
    "reddit_wholesome": 0,
    "helpful": 0,
    "truthnuke": 0,
    "truke": 0,
    "true": 0,
    "false": 0,
    "up": 0.25,
    "arrow_up": 0.5,
    "arrow_down": -0.5,
}

KARMIC_MILESTONE = {
    50,
    100,
    250,
    500,
    1000,
    10000,
    100000,
    1000000,
    10000000,
    100000000,
    1000000000,
    10000000000,
    100000000000,
}

UPVOTE_STR = "<:reddit_upvote:1266139689136689173>"
DOWNVOTE_STR = "<:reddit_downvote:1266139651660447744>"
SILVER_STR = "<:reddit_silver:833677163739480079>"
GOLD_STR = "<:reddit_gold:833675932883484753>"
PLAT_STR = "<:reddit_platinum:833678610279563304>"
WHOLESOME_STR = "<:reddit_wholesome:833669115762835456>"
HELPFUL_STR = "<:helpful:1412197811008704694>"
TRUKE_STR = "<:truke:1359507023951298700>"
TRUE_STR = "<:true:1389941856963526757>"
FALSE_STR = "<:false:1389942082059243550>"


class Analyse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.message_count = 0

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, "analysis_finished"):
            self.bot.analysis_finished = asyncio.Event()
            self.bot.loop.create_task(self.run_analysis())

    async def run_analysis(self):
        try:
            async with karma_lock:
                # Load Karmic Deductions
                try:
                    with open("deductions.json", "r", encoding="utf-8") as f:
                        deductions = json.load(f)
                except FileNotFoundError:
                    self.logger.warning("SHIT, I LOST THE KARMIC ARCHIVES")
                    deductions = {}
                except json.JSONDecodeError:
                    self.logger.exception("FAILED TO DECODE KARMIC ARCHIVES")
                    deductions = {}

                for guild in self.bot.guilds:
                    guild_deductions = deductions.get(guild.id, {})

                    for user, deduction in guild_deductions.items():
                        user_obj = guild.get_member_named(user)
                        if user_obj is not None:
                            karmic_dict[guild.id][user_obj.id]["Karma"] += deduction
                        else:
                            self.logger.warning(
                                f"USER {user} NOT IN SUBREDDIT {guild.name}"
                            )

                self.logger.info("COUNTING KARMA...")
                for guild in self.bot.guilds:
                    for channel in guild.text_channels:
                        try:
                            async for message in channel.history(
                                limit=None, oldest_first=True
                            ):
                                await self._analyse_message(guild, message)

                                self.message_count += 1

                                if self.message_count % 1000 == 0:
                                    await self.bot.change_presence(
                                        activity=discord.Game(
                                            name=f"{self.message_count} MESSAGES ANALYSED"
                                        ),
                                    )
                                    self.logger.info(
                                        f'CHANGED STATUS: "{self.message_count} MESSAGES ANALYSED"'
                                    )

                        except discord.HTTPException:
                            self.logger.exception(
                                f"HTTP ERROR fetching history for channel {channel.name} in {guild.name}"
                            )
                        except Exception:
                            self.logger.exception(
                                f"Unexpected error analyzing history for channel {channel.name} in {guild.name}"
                            )
        finally:
            self.logger.info("FINISHED COUNTING KARMA")
            self.bot.analysis_finished.set()

    async def _analyse_message(self, guild, message):
        self.logger.debug(f"({self.message_count}) {message.author}: {message.content}")
        # Ignore Deleted Users and messages sent after bot initialisation.
        if message.author.name == "Deleted User" or message.created_at > self.init_time:
            self.logger.debug("Ignoring irrelevant message")
            return

        # Count Messages
        karmic_dict[guild.id][message.author.id]["Messages"] += 1

        for reaction in message.reactions:
            emoji_name = (
                reaction.emoji
                if isinstance(reaction.emoji, str)
                else reaction.emoji.name
            )

            # Ignore Non-Karmic Reactions
            if emoji_name not in reaction_dict:
                continue

            # Count multiple truke reactions as a single truke
            if emoji_name in ("truthnuke", "truke"):
                karmic_dict[guild.id][message.author.id]["truke"] += 1
                continue

            try:
                # Add Karma
                async for user in reaction.users():
                    # Skip Self Reactions
                    if user == message.author:
                        continue

                    # Add Reaction Count
                    karmic_dict[guild.id][message.author.id][emoji_name] += 1
                    # Add Weighted Karma Value
                    karmic_dict[guild.id][message.author.id]["Karma"] += reaction_dict[
                        emoji_name
                    ]

                    # Count Reactions given
                    karmic_dict[guild.id][user.id][emoji_name] += 1
                    karmic_dict[guild.id][user.id]["Karma"] += reaction_dict[emoji_name]

            except discord.HTTPException:
                self.logger.exception(
                    f"HTTP ERROR fetching reaction users for message {message.id}"
                )
            except Exception:
                self.logger.exception(
                    f"Unexpected error analyzing message {message.id}"
                )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self._handle_reaction(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self._handle_reaction(payload, add=False)

    async def _handle_reaction(self, payload, add=True):
        if not payload.guild_id:
            return

        # Ignore Non-Karmic Reactions
        if payload.emoji.name not in reaction_dict:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        message = await guild.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )

        if user == message.author:
            return

        async with karma_lock:
            # Count Reactions
            guild_id = payload.guild_id
            author_id = payload.message_author_id

            # Add or remove karma and reaction counts
            karmic_dict[guild_id][author_id][payload.emoji.name] += 1
            karmic_dict[guild_id][author_id]["Karma"] += reaction_dict[
                payload.emoji.name
            ]

            if karmic_dict[guild_id][author_id]["Karma"] in KARMIC_MILESTONE:
                if (
                    karmic_dict[guild_id][author_id]["Karma"]
                    > karmic_dict[guild_id][author_id]["Karma_milestone"]
                ):
                    await self._karma_milestone(
                        message, karmic_dict[guild_id][author_id]["Karma"]
                    )

        action = "ANALYSED" if add else "UN-ANALYSED"
        self.logger.debug(
            f"{action} {user.name}'S REACTION TO {message.author.name}'S POST"
        )

    async def _karma_milestone(self, message, karma):
        await message.channel.send(
            f"KARMIC MILESTONE ALERT! REDDITOR {message.author.mention} "
            f"HAS REACHED {karma} KARMA {' '.join([UPVOTE_STR] * 5)} "
        )
        karmic_dict[message.guild.id][message.author.id]["Karma_milestone"] = karma

    @commands.Cog.listener()
    async def on_message(self, message):
        await self._handle_message(message, add=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await self._handle_message(message, add=False)

    async def _handle_message(self, message, add=True):
        if not message.guild:
            return

        modifier = 1 if add else -1
        self.message_count += modifier

        # Update User's message count
        async with karma_lock:
            karmic_dict[message.guild.id][message.author.id]["Messages"] += modifier

        action = "ANALYSED" if add else "UN-ANALYSED"
        self.logger.debug(f"{action} MESSAGE: {message.author.name}: {message.content}")

    async def _get_users_to_iterate(self, ctx):
        users_to_iterate = set()

        # @everyone
        if "@everyone" in ctx.message.content:
            users_to_iterate.update(
                m.id
                for m in ctx.guild.members
                if karmic_dict[ctx.guild.id][m.id]["Messages"] >= 100
            )

        # @here
        elif "@here" in ctx.message.content:
            users_to_iterate.update(
                m.id for m in ctx.guild.members if m.status != discord.Status.offline
            )

        else:
            # @user
            users_to_iterate.update(m.id for m in ctx.message.mentions)

            # @role
            for role in ctx.message.role_mentions:
                users_to_iterate.update(m.id for m in role.members)

            # No Arguments
            if not users_to_iterate:
                users_to_iterate.add(ctx.author.id)

        return users_to_iterate

    def _get_user_string(self, guild, user_id):
        user_obj = guild.get_member(user_id)
        return user_obj.display_name if user_obj else str(user_id)

    async def _handle_karma_lock(self, reply):
        if karma_lock.locked():
            await reply.edit(
                content="WAITING TO ACCESS KARMIC ARCHIVES, "
                "THIS MAY TAKE LONGER THAN USUAL"
            )

    @commands.command(aliases=["analysis"])
    async def analyse(self, ctx):
        """
        Analyse a user's karma
        - `user` (optional): Mention the user(s) to analyse.
        """
        reply = await ctx.reply("KARMA SUBROUTINE INITIALISED")

        await self._handle_karma_lock(reply)

        async with karma_lock:
            users_to_iterate = await self._get_users_to_iterate(ctx)

            self.logger.info(f"ANALYSING USERS: {users_to_iterate}")

            await asyncio.sleep(random.uniform(2.5, 5))
            await reply.edit(content="KARMA ANALYSED")

            for user in users_to_iterate:
                user_data = karmic_dict[ctx.guild.id][user]
                messages = user_data["Messages"]
                karma = user_data["Karma"]

                user_str = self._get_user_string(ctx.guild, user)

                karma_ratio = karma / messages if messages != 0 else 0
                karma_str = UPVOTE_STR if karma >= 0 else DOWNVOTE_STR

                # Create Karmic analysis embed for each user
                embed = discord.Embed(
                    title=f"{user_str}",
                    color=REDDIT_RED,
                )

                # Karma/Reactions Earned
                fields = [
                    ("Karma", f"{karma} {karma_str}", False),
                    ("Messages", f"{messages}", False),
                    ("Karmic Ratio", f"{round(karma_ratio, 4)}", False),
                    ("Silver", f"{user_data['reddit_silver']} {SILVER_STR}", True),
                    ("Gold", f"{user_data['reddit_gold']} {GOLD_STR}", True),
                    ("Platinum", f"{user_data['reddit_platinum']} {PLAT_STR}", True),
                    (
                        "Wholesome",
                        f"{user_data['reddit_wholesome']} {WHOLESOME_STR}",
                        True,
                    ),
                    ("Helpful", f"{user_data['helpful']} {HELPFUL_STR}", True),
                    ("Trukes", f"{user_data['truke']} {TRUKE_STR}", True),
                    ("Karma_given", f"{karma} {karma_str}", False),
                    (
                        "Silver_given",
                        f"{user_data['reddit_silver']} {SILVER_STR}",
                        True,
                    ),
                    ("Gold_given", f"{user_data['reddit_gold']} {GOLD_STR}", True),
                    (
                        "Platinum_given",
                        f"{user_data['reddit_platinum']} {PLAT_STR}",
                        True,
                    ),
                    (
                        "Wholesome_given",
                        f"{user_data['reddit_wholesome']} {WHOLESOME_STR}",
                        True,
                    ),
                    ("Helpful_given", f"{user_data['helpful']} {HELPFUL_STR}", True),
                    ("Trukes_given", f"{user_data['truke']} {TRUKE_STR}", True),
                ]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                try:
                    await ctx.channel.send(embed=embed)
                except discord.HTTPException as e:
                    self.logger.error(f"FAILED TO SEND EMBED: {e}")

    @commands.command(
        aliases=[
            "truth",
            "truths",
            "trukes",
            "truthnuke",
            "truthnukes",
            "false",
            "falses",
        ]
    )
    async def truke(self, ctx):
        """
        Analyse a user's truthfulness
        - `user` (optional): Mention the user(s) to analyse.
        """
        reply = await ctx.reply("TRUTHFULNESS SUBROUTINE INITIALISED")

        await self._handle_karma_lock(reply)

        async with karma_lock:
            users_to_iterate = await self._get_users_to_iterate(ctx)

            self.logger.info(f"ANALYSING USERS: {users_to_iterate}")

            await asyncio.sleep(random.uniform(2.5, 5))
            await reply.edit(content="TRUTHFULNESS ANALYSED")

            for user in users_to_iterate:
                user_data = karmic_dict[ctx.guild.id][user]
                truth = user_data["true"]
                false = user_data["false"]
                truke = user_data["truke"]
                truth_nuke = user_data["truthnuke"]

                user_str = self._get_user_string(ctx.guild, user)

                # Create Karmic analysis embed for each user
                embed = discord.Embed(
                    title=f"{user_str}",
                    color=REDDIT_RED,
                )

                # Karma/Reactions Earned
                fields = [
                    ("Truths", f"{truth} {TRUE_STR}", False),
                    ("Truth Nukes", f"{truke + truth_nuke} {TRUKE_STR}", False),
                    ("Falses", f"{false} {FALSE_STR}", False),
                ]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                try:
                    await ctx.channel.send(embed=embed)
                except discord.HTTPException as e:
                    self.logger.error(f"FAILED TO SEND EMBED: {e}")

            misc_cog = self.bot.get_cog("Misc")
            if misc_cog:
                await misc_cog.change_status()


async def setup(bot):
    await bot.add_cog(Analyse(bot))
