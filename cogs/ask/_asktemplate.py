from discord.ext import commands

from askbot import AskCog


class AskTemplate(AskCog):
    def __init__(self, bot):
        system_instructions = """
        """
        super().__init__(bot, "template", system_instructions, valid_server_ids=[])

    @commands.command(hidden=True)
    async def asktemplate(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskTemplate(bot))
