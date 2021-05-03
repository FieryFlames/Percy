from discord import Color, AllowedMentions, User
from discord.ext import commands
from discord.ext.commands import ColorConverter
from discord.ext.commands.errors import BadColorArgument
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from profanity_check import predict_prob

from .utils.ciede2000 import rgb2lab, ciede2000
from .utils.models import Booster
from .utils.checks import is_allowed_role
from .utils.errors import BelowMember, TooManyRoles


class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(
            self.bot.engine, class_=AsyncSession, future=True)

    async def assure_role(self, member):
        guild = member.guild
        # get a member object of our bot user
        bot = guild.get_member(self.bot.user.id)
        bot_top_role = bot.roles[-1]  # bot's top role
        member_top_role = member.roles[-1]  # member's top role

        # failsafes
        if bot_top_role <= member_top_role:
            raise BelowMember
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
    @commands.guild_only()
    @is_allowed_role()
    @commands.bot_has_permissions(manage_roles=True)
    async def _rename(self, ctx, new_name):
        new_name = str(new_name)
        # make sure new name isnt too long
        if len(new_name) >= 101:
            await ctx.send("New name must be under 100 characters.", hidden=True)
            return

        if predict_prob([new_name]) >= 0.17:
            await ctx.send("Profanity detected, unable to rename your custom role to that.", hidden=True)
            return

        if new_name.lower() in ["dj", "bot commander", "giveaways", "cease customizing"] or new_name.lower().startswith("customizing permit"):
            await ctx.send("Blacklisted role name, unable to rename your custom role to that.", hidden=True)
            return

        # make sure that the user isn't trying to copy another role
        role_names = []
        for role in ctx.guild.roles:
            role_names.append(role.name.lower())

        if new_name.lower() in role_names:
            await ctx.send("There's already another role with that name, unable to rename your custom role to that.", hidden=True)
            return

        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.assure_booster(ctx.author)
        await self.assure_role(ctx.author)
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
    @commands.guild_only()
    @is_allowed_role()
    @commands.bot_has_permissions(manage_roles=True)
    async def _recolor(self, ctx, new_color):
        # try to get color in usable format
        try:
            new_color = await ColorConverter().convert(ctx, str(new_color))
        except (BadColorArgument):
            await ctx.send("Something's wrong with your color. Are you sure it's formatted in a way I can understand?", hidden=True)
            return
        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.assure_booster(ctx.author)
        await self.assure_role(ctx.author)
        # db stuff and actual recoloring
        async with self.sessionmaker() as session:
            async with session.begin():
                # Color similarity check stuff
                # get roles
                og_roles = ctx.guild.roles
                roles = []
                # get guild's boosters
                boosters_result = await session.execute(select(Booster).where(Booster.role_id != None, Booster.guild_id == ctx.guild.id))
                boosters = boosters_result.scalars().fetchall()
                # now we remove any default colored roles or custom roles from the roles variable
                for role in og_roles:
                    if role.color.value == 0:
                        continue
                    for row in boosters:
                        if row.role_id == role.id:
                            break
                    roles.append(role)
                # Now we compare to find the most similar role, and how similar it is
                closest_similarity = 99
                closest_role = None

                for role in roles:
                    role_lab = rgb2lab(role.color.to_rgb())
                    custom_role_lab = rgb2lab(new_color.to_rgb())
                    similarity = ciede2000(role_lab, custom_role_lab)
                    # update the closest stuff
                    if similarity <= closest_similarity:
                        closest_similarity = similarity
                        closest_role = role

                # check if it's too similar, and tell then return if it is
                if closest_similarity <= 3:
                    await ctx.send(f"That color is too similar to {closest_role.mention}, unable to recolor your custom role.", hidden=True, allowed_mentions=AllowedMentions.none())
                    return

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


def setup(bot):
    bot.add_cog(RoleManagement(bot))
