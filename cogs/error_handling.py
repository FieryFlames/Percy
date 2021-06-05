import sys
import traceback
from cogs.utils.errors import BelowVisibleRole, NotAllowedRole, NotBoosting, TooManyRoles
from discord.ext import commands


class ErrorHandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = self.bot.emoji

    # Error handler for common errors, more common errors go in commands themselves for now
    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"{self.emoji['Warn']} This command cannot be used in private messages")

        elif isinstance(error, NotBoosting):
            await ctx.send(f"{self.emoji['No']} This command is exclusive to boosters", hidden=True)

        elif isinstance(error, commands.BotMissingPermissions):
            #           list to string        remove [] remove '         remove _          capitalize
            perms_str = str(error.missing_perms)[
                1:][:-1].replace("'", '').replace("_", " ").capitalize()
            await ctx.send(f"{self.emoji['Warn']} I need the following permissions: {perms_str}", hidden=True)

        elif isinstance(error, commands.MissingPermissions):
            #           list to string        remove [] remove '         remove _          capitalize
            perms_str = str(error.missing_perms)[
                1:][:-1].replace("'", '').replace("_", " ").capitalize()
            await ctx.send(f"{self.emoji['No']} You need the following permissions: {perms_str}", hidden=True)

        elif isinstance(error, BelowVisibleRole):
            await ctx.send(f"{self.emoji['Warn']} I can't give you a custom role as your visible role is above my top role", hidden=True)

        elif isinstance(error, TooManyRoles):
            await ctx.send(f"{self.emoji['Warn']} I can't give you a custom role as this server has hit the role cap of 250", hidden=True)

        elif isinstance(error, NotAllowedRole):
            await ctx.send(f"{self.emoji['No']} You can't customize your role at this time", hidden=True)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command', file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
