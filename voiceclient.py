import logging

import discord
from discord.ext import commands, voice_recv


VOICE_CLIENTS = {}


class VoiceClient:
    """
    Voice Client class to allow for server independent voice clients
    """

    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.guild = guild
        self.voice_client = None

        self.ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

    async def _join_vc(self, ctx):
        channel = ctx.author.voice.channel

        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel != channel:
                self.voice_client = await channel.connect(
                    cls=voice_recv.VoiceRecvClient
                )

        else:
            self.voice_client = await channel.connect()
