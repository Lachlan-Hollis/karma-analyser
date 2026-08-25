import logging

import discord
from discord.ext import commands


class Petition(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command()
    async def petition(self, ctx, *, text: str):
        """
        Create a petition
        - `text` (required): The petition text
        """
        if not text:
            return

        await self.create_petition(ctx.message, text)

    async def create_petition(self, message, text):
        try:
            reply = await message.reply(
                content=f"# {text}", file=discord.File("./petition.gif")
            )

            await reply.add_reaction("🖊️")
        except discord.Forbidden:
            self.logger.warning(
                f"Missing permissions to create petition in {message.channel.id}"
            )
        except discord.HTTPException:
            self.logger.exception(f"Failed to create petition in {message.channel.id}")
        except Exception:
            self.logger.exception("Unexpected error in petition command")


async def setup(bot):
    await bot.add_cog(Petition(bot))
