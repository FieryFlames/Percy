import argparse

import discord
import toml
from discord.ext import commands
from discord_slash import SlashCommand
from sqlalchemy.ext.asyncio import create_async_engine
import traceback
import sys
from cogs.utils.models import Base
from cogs.utils.errors import BelowMember, NotBoosting, NotAllowedRole, TooManyRoles
# define some stuff
parser = argparse.ArgumentParser(description="Percy Launcher")

# add arguments
parser.add_argument(
    "--config", help="Use a differect config other than the default one.", default="configs/percy.toml")
# parse
args = parser.parse_args()
# read conf
with open(args.config) as conf_file:
    config = toml.load(conf_file)

token = config["Discord"]["Token"]
url = config["SQLAlchemy"]["URL"]
color = config["Bot"]["Color"]
cogs = config["Bot"]["Cogs"]
emoji = config["Emoji"]
# actual bot


class BBot(commands.Bot):
    def __init__(self, url, color, emoji, cogs):
        # set intents
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents, command_prefix=commands.when_mentioned)

        # Remove help command
        self.remove_command('help')

        # Database load
        self.engine = create_async_engine(url, future=True)

        # color
        self.color = color

        self.emoji = emoji

        # add slash commands
        SlashCommand(self, sync_commands=True)

        for cog in cogs:
            self.load_extension(cog)

    async def on_connect(self):
        # Create the table if it doesn't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # set the activity
        activity = discord.Activity(
            type=discord.ActivityType.listening, name=f"boost events")
        await self.change_presence(status=discord.Status.idle, activity=activity)

    async def on_ready(self):
        print("Ready!")

    # Error handler for common errors, more common errors go in commands themselves for now
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

        elif isinstance(error, BelowMember):
            await ctx.send(f"{self.emoji['Warn']} I can't give you a custom role as your top role is above mine", hidden=True)

        elif isinstance(error, TooManyRoles):
            await ctx.send(f"{self.emoji['Warn']} I can't give you a custom role as this server has hit the role cap of 250", hidden=True)

        elif isinstance(error, NotAllowedRole):
            await ctx.send(f"{self.emoji['No']} You can't customize your role at this time", hidden=True)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command', file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)


bot = BBot(url, color, emoji, cogs)

bot.run(token)
