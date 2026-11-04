import logging

import aiohttp
import discord
from discord.ext import commands


class Insult(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command()
    async def insult(self, ctx, user: discord.Member = None):
        """
        Insult a fellow Redditor
        - `user` (optional): The Redditor to insult
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://evilinsult.com/generate_insult.php?lang=en&type=json"
                ) as resp:
                    if resp.status != 200:
                        await ctx.reply(content="ERROR, CAN'T INSULT USER")
                        self.logger.error(f"ERROR, CAN'T INSULT USER: {resp.status}")
                        return
                    data = await resp.json()
                    insult = data.get("insult", "ERROR, CAN'T INSULT USER")
        except aiohttp.ClientError:
            self.logger.exception("HTTP Error fetching insult")
            await ctx.reply("Failed to fetch insult from API")
            return
        except Exception:
            self.logger.exception("Unexpected error fetching insult")
            return

        try:
            if user is None:
                await ctx.reply(content=insult)
                self.logger.info(f"INSULT: {insult}")
            else:
                await ctx.reply(f"{user.mention}: {insult}")
                self.logger.info(f"INSULTING USER {user.name}: {insult}")
        except discord.HTTPException:
            self.logger.exception(f"Failed to send insult to {ctx.author.name}")
        except Exception:
            self.logger.exception("Unexpected error in insult command")


async def setup(bot):
    await bot.add_cog(Insult(bot))
