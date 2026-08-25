import logging
import random

import aiohttp
import discord
from discord.ext import commands


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command()
    async def wordle(self, ctx):
        """
        Get a random wordle answer
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/c46f451920d5cf6326d550fb2d6abb1642717852/wordle-answers-alphabetical.txt"
                ) as resp:
                    if resp.status != 200:
                        await ctx.reply(content="NONCE")
                        self.logger.error(
                            f"Failed to fetch wordle answers: {resp.status}"
                        )
                        return

                    text = await resp.text()
                    words = [
                        line.strip().lower()
                        for line in text.splitlines()
                        if line.strip()
                    ]
        except aiohttp.ClientError:
            self.logger.exception("HTTP Error fetching wordle answers")
            await ctx.reply("Failed to fetch wordle answers")
            return
        except Exception:
            self.logger.exception("Unexpected error fetching wordle answers")
            return

        try:
            await ctx.reply(content=random.choice(words).upper())
        except discord.HTTPException:
            self.logger.exception(f"Failed to send wordle answer to {ctx.author.name}")
        except Exception:
            self.logger.exception("Unexpected error in wordle command")


async def setup(bot):
    await bot.add_cog(Wordle(bot))
