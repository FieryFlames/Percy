import argparse

import discord
import toml
from discord.ext import commands
from discord_slash import SlashCommand
from sqlalchemy.ext.asyncio import create_async_engine
import traceback
import sys
from cogs.utils.models import Base
from cogs.utils.errors import BelowVisibleRole, NotBoosting, NotAllowedRole, TooManyRoles
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


bot = BBot(url, color, emoji, cogs)

bot.run(token)
