import logging

import discord
from discord.ext import commands

import utils


class Gifs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command(aliases=["gif", "pic", "pics", "picture", "pictures"])
    async def gifs(self, ctx, *, text: str = None):
        """
        Search for gifs
        - `text` (required): The gif to search for. Defaults to a random gif.
        """
        try:
            gif_url = await utils.gif_search(text)
            if gif_url:
                await ctx.message.reply(gif_url)
            else:
                await ctx.message.reply("No gif found, try again")
        except discord.HTTPException:
            self.logger.exception(f"Failed to reply with GIF in {ctx.channel.name}")
        except Exception:
            self.logger.exception("Unexpected error in gifs command")


async def setup(bot):
    await bot.add_cog(Gifs(bot))
