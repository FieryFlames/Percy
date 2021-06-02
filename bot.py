import argparse
import sys
import traceback
from colorama import init, Fore, Back, Style

import discord
from sqlalchemy import except_
import toml
from art import text2art
from discord.ext import commands
from discord_slash import SlashCommand
from sqlalchemy.ext.asyncio import create_async_engine

from cogs.utils.models import Base

init(autoreset=True)

print(Fore.GREEN + text2art("Percy"))

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


class Percy(commands.Bot):
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

        print(Fore.WHITE + "-- COGS --")
        for cog in cogs:
            try:
                self.load_extension(cog)
                print(Fore.GREEN + f"Successfully loaded " + Fore.WHITE + cog)

            except Exception as error:
                print('Ignoring exception in cog', file=sys.stderr)
                traceback.print_exception(
                    type(error), error, error.__traceback__, file=sys.stderr)
                print(Fore.RED + "Failed to load " + Fore.WHITE + cog)
        
        print(Fore.WHITE + "-- LOGS --")

    async def on_connect(self):
        print(Fore.GREEN + "Connected as " + Fore.WHITE + str(self.user))
        # Create the table if it doesn't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # set the activity
        activity = discord.Activity(
            type=discord.ActivityType.listening, name=f"boost events")
        await self.change_presence(status=discord.Status.idle, activity=activity)

    async def on_disconnect(self):
        print(Fore.RED + "Disconnected")

    async def on_ready(self):
        print(Fore.GREEN + "Ready")

bot = Percy(url, color, emoji, cogs)

bot.run(token)
