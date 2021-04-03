from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from .utils.models import Booster

guild_ids = [734485213304062053]


class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)
    
    async def assure_booster(self, member):
        async with self.sessionmaker() as session:
            # Get the boooster
            booster = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == member.guild_id))
            # if no booster is returned we make one
            if booster == None:
                booser = Booster(guild_id=member.guild.id, user_id=member.id)
                # add booster to the db
                await session.add(booster) 
            await session.commit()

    @cog_ext.cog_subcommand(guild_ids=guild_ids, base="role", name="rename", description="Rename your custom role.",
                            options=[
                                create_option(
                                    name="name",
                                    description="New name for your custom role.",
                                    option_type=3,
                                    required=True
                                )
                            ])
    async def _rename(self, ctx, new_name):
        return

    @cog_ext.cog_subcommand(guild_ids=guild_ids, base="role", name="recolor", description="Recolor your custom role.",
                            options=[
                                create_option(
                                    name="color",
                                    description="New color for your custom role.",
                                    option_type=3,
                                    required=True
                                )
                            ])
    async def _recolor(self, ctx, new_color):
        return

    # TODO: Implement role sharing, https://trello.com/c/0uGdMGx2/9-role-sharing
    # @cog_ext.cog_subcommand(guild_ids=guild_ids, base="role", name="share", description="Share your custom role.",
    #                        options=[
    #                            create_option(
    #                                name="member",
    #                                description="Member who you'd like to share your custom role with.",
    #                                option_type=6,
    #                                required=True
    #                            )
    #                        ])
    # async def _share(self, ctx, extra_user):
    #    return


def setup(bot):
    bot.add_cog(RoleManagement(bot))
