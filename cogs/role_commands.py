from discord import Color, AllowedMentions, Embed
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


class RoleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(
            self.bot.engine, class_=AsyncSession, future=True)
        self.role_management = self.bot.get_cog("RoleCommon")

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
    async def _rename(self, ctx, name):
        new_name = name
        # make sure new name isnt too long
        if len(new_name) >= 101:
            await ctx.send(f"{self.bot.emoji['No']} New name must be under 100 characters.", hidden=True)
            return

        if predict_prob([new_name]) >= 0.17:
            await ctx.send(f"{self.bot.emoji['No']} Profanity detected, unable to rename your custom role to that.", hidden=True)
            return

        if new_name.lower() in ["dj", "bot commander", "giveaways", "cease customizing"] or new_name.lower().startswith("customizing permit"):
            await ctx.send(f"{self.bot.emoji['No']} Blacklisted role name, unable to rename your custom role to that.", hidden=True)
            return

        # make sure that the user isn't trying to copy another role
        role_names = []
        for role in ctx.guild.roles:
            role_names.append(role.name.lower())

        if new_name.lower() in role_names:
            await ctx.send(f"{self.bot.emoji['No']} There's already another role with that name, unable to rename your custom role to that.", hidden=True)
            return

        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.role_management.assure_booster(ctx.author)
        await self.role_management.assure_role(ctx.author)
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
        await ctx.send(f"{self.bot.emoji['Yes']} Renamed your custom role.", hidden=True)  # alert user

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
    async def _recolor(self, ctx, color):
        # try to get color in usable format
        try:
            new_color = await ColorConverter().convert(ctx, str(color))
        except (BadColorArgument):
            await ctx.send(f"{self.bot.emoji['Warn']} Something's wrong with your color. Are you sure it's formatted in a way I can understand?", hidden=True)
            return
        await ctx.defer(hidden=True)
        # make sure we have the booster and the role is alright
        await self.role_management.assure_booster(ctx.author)
        await self.role_management.assure_role(ctx.author)
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
                # make a list of custom role ids so we can ignore them
                custom_role_ids = []
                for booster in boosters:
                    if booster.role_id != 0:
                        custom_role_ids.append(booster.role_id)

                # now we remove any default colored roles or custom roles from the roles variable
                for role in og_roles:
                    if role.color.value == 0:
                        continue
                    if role.id in custom_role_ids:
                        continue
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
                    await ctx.send(f"{self.bot.emoji['No']} That color is too similar to {closest_role.mention}, unable to recolor your custom role.", hidden=True, allowed_mentions=AllowedMentions.none())
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
        # TODO: revisit having embed for the role color?
        # embed = Embed(description=f"{self.bot.emoji['Yes']} Recolored your custom role.", color=custom_role.color)
        await ctx.send(f"{self.bot.emoji['Yes']} Recolored your custom role.", hidden=True)


def setup(bot):
    bot.add_cog(RoleCommands(bot))
