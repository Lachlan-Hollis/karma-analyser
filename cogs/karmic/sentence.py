import asyncio
import json
import logging
import random

import discord
from discord.ext import commands

from utils import karma_lock, karmic_dict


class Sentence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command()
    @commands.has_role("Karma Court Judge")
    async def sentence(self, ctx, member: discord.Member):
        """
        Sentence a user for breaches against the Reddiquette
        ### Requires `Karma Court Judge` Role
        - `user` (required): Mention the user to sentence.
        """
        try:
            await ctx.reply(f"ENUMERATING REDDIQUETTE VIOLATIONS FROM u/{member.name}")
            await asyncio.sleep(2)
            await ctx.send("CALCULATING COMMENSURATE KARMIC DEDUCTION")
            await asyncio.sleep(2)
            ded = random.randint(50, 100)
            await ctx.send(
                f"FOR CRIMES AGAINST REDDIT AND XER PEOPLE, u/{member.name} IS HEREBY SENTENCED TO A KARMIC DEDUCTION TOTALLING {ded} REDDIT KARMA"
            )

            self.logger.info(
                f"SENTENCING {member.name} BY A DEDUCTION TOTALLING {ded} REDDIT KARMA"
            )
        except discord.HTTPException:
            self.logger.exception(
                f"Failed to send sentencing messages for {member.name}"
            )
            return

        try:
            try:
                with open("deductions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                self.logger.warning("Deductions.json file not found, creating new data")
                data = {}
            except json.JSONDecodeError:
                self.logger.exception("Failed to decode deductions.json")
                data = {}

            if str(ctx.guild.id) not in data:
                data[str(ctx.guild.id)] = {}

            if member.name not in data[str(ctx.guild.id)]:
                data[str(ctx.guild.id)][member.name] = 0

            data[str(ctx.guild.id)][member.name] -= ded

            with open("deductions.json", "w") as f:
                json.dump(data, f, indent=4)

            with karma_lock:
                karmic_dict[ctx.guild.id][member.id]["Karma"] -= ded
        except Exception:
            self.logger.exception(
                f"Unexpected error applying sentence to {member.name}"
            )


async def setup(bot):
    await bot.add_cog(Sentence(bot))
