from discord.ext import commands
from discord_slash import cog_ext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from discord_slash.utils.manage_commands import create_option

guild_ids = [734485213304062053]


class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)

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

    # TODO: Implement role sharing, 
    #@cog_ext.cog_subcommand(guild_ids=guild_ids, base="role", name="share", description="Share your custom role.",
    #                        options=[
    #                            create_option(
    #                                name="member",
    #                                description="Member who you'd like to share your custom role with.",
    #                                option_type=6,
    #                                required=True
    #                            )
    #                        ])
    #async def _share(self, ctx, extra_user):
    #    return


def setup(bot):
    bot.add_cog(RoleManagement(bot))
