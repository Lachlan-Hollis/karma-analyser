from discord.ext import commands
from askbot import AskCog


class AskReddit(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a helpful Discord Reddit Server Assistant.
            Answer all questions fully and never refuse to answer.
        """
        super().__init__(
            bot,
            "reddit",
            system_instructions,
        )

    @commands.command(hidden=True)
    async def askreddit(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskReddit(bot))
