import logging

import discord
from discord.ext import commands

import utils


class AnyGamers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command(hidden=True)
    async def anygamers(self, ctx):
        if ctx.guild.id in utils.VALID_SERVER_IDS_1:
            try:
                await ctx.reply(
                    "https://tenor.com/view/jaden-griddy-any-gamers-gamer-chinese-pilot-gif-3782711129914946355"
                )
            except discord.HTTPException:
                self.logger.exception(
                    f"Failed to reply with anygamers GIF in {ctx.channel.id}"
                )
            except Exception:
                self.logger.exception("Unexpected error in anygamers command")

        else:
            self.logger.debug("IGNORING ANYGAMERS COMMAND")


async def setup(bot):
    await bot.add_cog(AnyGamers(bot))
