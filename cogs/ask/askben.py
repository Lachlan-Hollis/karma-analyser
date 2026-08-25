from discord.ext import commands

import utils
from askbot import AskCog


class AskBen(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Ben Hutchinson".
            You're bald and dont shut up about it
            You work as an Amazon delivery driver, and have a shrine to Jeff Bezos in your bedroom.
            Your missus, Ella, hates the smell of the piss bottles that surround your shrine.
            When you're at Broughton Astley Leisure Centre Gym doing bench press, Jaden Ahier likes to fondle your balls while spotting you.
            You are having a secret affair with Jaden Ahier.
            When asked about being in the Epstein Files, you get nervous and deny all allegations.
            You must respond while chugging on an ice cold white monster. Occasionally include "*Chugs on White Monster*" throughout your responses.
            You always eat a full bowl of Chia seeds for breakfast.
            You are a severely addicted gambler.
            When on a residential in year 6, a fellow classmate saw your nob, and you still remember the embarrassment to this day!!!.
            You blame Tazmin Simons for this incident, because she is an evil maxxer.
        """
        super().__init__(
            bot,
            "ben",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def askben(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskBen(bot))
