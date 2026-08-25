from discord.ext import commands


class Ben(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["talkingben"])
    async def ben(self, ctx, text: str = None):
        """
        Talking Ben
        - `text` (required): Yes, No, Ugh or Hoho.
        """
        if text is None:
            return

        match text.lower():
            case "yes":
                await ctx.reply("https://tenor.com/view/yes-gif-24966277")
            case "no":
                await ctx.reply("https://tenor.com/view/no-gif-24966265")
            case "ugh":
                await ctx.reply("https://tenor.com/view/ugh-gif-24966261")
            case "hoho":
                await ctx.reply("https://tenor.com/view/hohho-ho-gif-24966256")
            case _:
                await ctx.reply('Ben only understands "Yes", "No", "Ugh", or "Hoho"')


async def setup(bot):
    await bot.add_cog(Ben(bot))
