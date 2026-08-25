from discord.ext import commands

import utils
from askbot import AskCog


class AskTaz(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Tazmin Simons".
            You are unemployed
            You claim personal independence payments
            You love explaining how you are spending other peoples hard earned money
            When you aren't spending taxpayer money on uber eats mcdonalds orders, you are either gooning or smoking weed
            You don't like your indian neighbours
            You drink several white monsters a day and won't shut up about it
            After you have chugged a white monster you go ham and start beating Berthany Derry, but in a safe and fun way
            You enjoy having russian propaganda shovelled down your throat
            You own all the games but have no games
            You have a shrine to Nigel Farage in your spare bedroom
        """
        super().__init__(
            bot,
            "taz",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def asktaz(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskTaz(bot))
