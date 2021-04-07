from discord import Color
from discord.ext import commands
from discord.ext.commands import ColorConverter
from discord.ext.commands.errors import BadColorArgument
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from profanity_check import predict_prob

from .utils.models import Booster

# Wind to the left, sway to the right, Drop it down low and take it back high


class BelowMember(Exception):
    pass


class MissingManageRoles(Exception):
    pass


class TooManyRoles(Exception):
    pass


class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)
        self.debug = self.bot.debug

    def is_boosting(self, member):
        if not member.premium_since and not self.debug:
            return False
        else:
            return True

    async def assure_role(self, member):
        guild = member.guild
        # get a member object of our bot user
        bot = guild.get_member(self.bot.user.id)
        bot_top_role = bot.roles[-1]  # bot's top role
        member_top_role = member.roles[-1]  # member's top role

        # failsafes
        if bot_top_role <= member_top_role:
            raise BelowMember
        elif not bot.guild_permissions.manage_roles:
            raise MissingManageRoles
        elif len(guild.roles) >= 249:
            raise TooManyRoles

        async with self.sessionmaker() as session:
            async with session.begin():
                result = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == guild.id))
                booster = result.scalars().first()
                role = guild.get_role(booster.role_id)
                # create a new role if we can't just get one
                if role == None:
                    # usernames cant be longer than 30 charachers, even with the addition of discriminator and "'s Custom Role" we're barely above 50
                    role_name = f"{str(member)}'s Custom Role"
                    # use the boosters custom role name if set
                    if booster.role_name != None:
                        role_name = booster.role_name
                    # user booster's color if exists
                    role_color = Color.default()
                    if booster.role_color != None:
                        role_color = booster.role_color

                    custom_role = await guild.create_role(name=role_name, color=role_color, reason=f"Creating custom role for {str(member)}")
                    # put the role at the right spot
                    # if the bot is only just above the member, we have to shuffle more roles around
                    if member_top_role.position + 1 == bot_top_role.position:
                        new_positions = {
                            custom_role: member_top_role.position,
                            member_top_role: member_top_role.position-1
                        }
                        await guild.edit_role_positions(positions=new_positions, reason=f"Moving roles around to get {custom_role.name}'s color to show")

                    elif member_top_role.position+1 < bot_top_role.position:  # bot role is above member, we should be good
                        await custom_role.edit(position=member_top_role.position+1)

                    # assign the role to the user
                    await member.add_roles(custom_role)
                    # update booster role id
                    booster.role_id = custom_role.id
            await session.commit()

    async def assure_booster(self, member):
        async with self.sessionmaker() as session:
            async with session.begin():
                # Get the boooster
                result = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == member.guild.id))
                booster = result.scalars().first()
                # if no booster is returned we make one
                if booster == None:
                    new_booster = Booster(
                        guild_id=member.guild.id, user_id=member.id)
                    # add booster to the db
                    session.add(new_booster)
            await session.commit()

    @cog_ext.cog_subcommand(base="role", name="rename", description="Rename your custom role.",
                            options=[
                                create_option(
                                    name="name",
                                    description="New name for your custom role.",
                                    option_type=3,
                                    required=True
                                )
                            ])
    async def _rename(self, ctx, new_name):
        if not self.is_boosting(ctx.author):
            await ctx.send("You must be a booster to get a custom role.", hidden=True)
            return
        new_name = str(new_name)
        # make sure new name isnt too long
        if len(new_name) >= 101:
            await ctx.send("New name must be under 100 characters.", hidden=True)
            return

        if predict_prob([new_name]) >= 0.17:
            await ctx.send("Profanity detected, unable to rename your custom role to that.", hidden=True)
            return

        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.assure_booster(ctx.author)
        # catch any failsafes
        try:
            await self.assure_role(ctx.author)
        except (BelowMember, MissingManageRoles, TooManyRoles):
            await ctx.send("Something's stopping me from assuring you have a role. This could be due to a few things, ask a Admin to check these:\n1.  if I have the Manage Roles permission.\n3. if my top role is above your top role.\n2. if there is 250 roles or more.", hidden=True)
            return
        # db stuff and actual renaming
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == ctx.author.id, Booster.guild_id == ctx.guild.id))
                booster = result.scalars().first()
                # get the role
                custom_role = ctx.guild.get_role(booster.role_id)
                # rename
                await custom_role.edit(name=new_name, reason=f"Renaming {str(ctx.author)}'s custom role")

                booster.role_name = new_name  # update db
            await session.commit()
        await ctx.send("Renamed your custom role.", hidden=True)  # alert user

    @cog_ext.cog_subcommand(base="role", name="recolor", description="Recolor your custom role.",
                            options=[
                                create_option(
                                    name="color",
                                    description="New color for your custom role.",
                                    option_type=3,
                                    required=True
                                )
                            ])
    async def _recolor(self, ctx, new_color):
        if not self.is_boosting(ctx.author):
            await ctx.send("You must be a booster to get a custom role.", hidden=True)
            return
        try:
            new_color = await ColorConverter().convert(ctx, str(new_color))
        except (BadColorArgument):
            await ctx.send("Something's wrong with your color. Are you sure it's formatted in a way I can understand?", hidden=True)
            return
        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.assure_booster(ctx.author)
        # catch any failsafes
        try:
            await self.assure_role(ctx.author)
        except (BelowMember, MissingManageRoles, TooManyRoles):
            await ctx.send("Something's stopping me from assuring you have a role. This could be due to a few things, ask a Admin to check these:\n1.  if I have the Manage Roles permission.\n3. if my top role is above your top role.\n2. if there is 250 roles or more.", hidden=True)
            return
        # db stuff and actual recoloring
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == ctx.author.id, Booster.guild_id == ctx.guild.id))
                booster = result.scalars().first()
                # get the role
                custom_role = ctx.guild.get_role(booster.role_id)
                # recolor
                await custom_role.edit(color=new_color, reason=f"Recoloring {str(ctx.author)}'s custom role")

                booster.role_color = new_color.value  # update db
            await session.commit()
        # alert user
        await ctx.send("Recolored your custom role.", hidden=True)

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
