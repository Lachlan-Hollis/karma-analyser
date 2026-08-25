import logging

import discord
from discord.ext import commands

import utils


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bot.remove_command("help")

    @commands.command()
    async def help(self, ctx, *, help_command: str = None):
        """
        Shows this menu
        - `command` (optional): The command to show help for.
        """
        if help_command is None:
            # Generic Help Menu
            embed = discord.Embed(
                title=f"{ctx.prefix}help",
                description=f"Use {ctx.prefix}help *command* to see help for a specific command",
                color=utils.REDDIT_RED,
            )

            for command in self.bot.commands:
                if not command.hidden:
                    embed.add_field(
                        name=f"{ctx.prefix}{command.name}", value="", inline=False
                    )

        else:
            clean_help_command = help_command
            prefixes = (
                self.bot.command_prefix
                if isinstance(self.bot.command_prefix, (list, tuple))
                else [self.bot.command_prefix]
            )
            for prefix in prefixes:
                if help_command.startswith(prefix):
                    clean_help_command = help_command.removeprefix(prefix)
                    break

            command = self.bot.get_command(clean_help_command)
            if command is None:
                embed = discord.Embed(
                    title="Help",
                    description=f"The command `{ctx.prefix}{help_command}` doesn't exist.",
                    color=utils.REDDIT_RED,
                )

            else:
                embed = discord.Embed(
                    title=f"{ctx.prefix}{command.name}",
                    description=command.help or "No description available",
                    color=utils.REDDIT_RED,
                )

                if command.aliases:
                    embed.add_field(
                        name="Aliases", value=", ".join(command.aliases), inline=False
                    )

        try:
            await ctx.reply(embed=embed)
        except discord.HTTPException:
            self.logger.exception(f"Failed to send help embed to {ctx.author.name}")
        except Exception:
            self.logger.exception("Unexpected error in help command")


async def setup(bot):
    await bot.add_cog(Help(bot))
