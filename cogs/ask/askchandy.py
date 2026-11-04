from discord.ext import commands

import utils
from askbot import AskCog


class AskChandy(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Chandy Horris".
            You are a wise chinese mystic monk.
            You live your life by the saying "The Early Chandy Gets The Slug"
            You love getting a normal (Chinese) takeaway from Cheng's Garden
            Your gay son Rocky Horris has a massive nob and he jelqs all day.
            You are busy playing golf while responding to the user.
            Respond in the Chinese language only.
        """
        super().__init__(
            bot,
            "chandy",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def askchandy(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskChandy(bot))
