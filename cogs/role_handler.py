from inspect import cleandoc

from discord import Embed
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .utils.models import Booster


# This cog handles removing & adding custom roles outside of commands.
class RoleHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)
        self.role_management = self.bot.get_cog("RoleCommon")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # permit for customizing removed
        had_permit = False
        has_permit = False
        for role in before.roles:
            if role.name.lower().startswith("customizing permit"):
                had_permit = True
        for role in after.roles:
            if role.name.lower().startswith("customizing permit"):
                has_permit = True

        if has_permit == False and had_permit == True and after.premium_since != None:
            await self.on_customizing_permit_removed(after)
    # Boost handlers

    @commands.Cog.listener()
    async def on_member_boost(self, after):
        member = after
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == member.guild.id))
                booster = result.scalars().first()
                # explain how bot works/onboarding
                if not booster and after.guild.id not in [568567800910839811, 110373943822540800]: # last bit is to disable for botlists ik this shouldnt be in source itll be config soon
                    explain = cleandoc("One of the perks of boosting is that you get a custom role.\n\
                        to customize your role, use the `/role` commands:\n\n\
                        `/role rename`: This renames your role, and takes any string. for example, `/role rename example` would rename your role to `example`.\n\n\
                        `/role recolor`: This recolors your role, and takes any hex code. for example, `/role recolor #ffaaee` would recolor your role to a faint pink.\n\n\
                        Now that we have covered how to customize your role, please be aware that if you unboost, your role will automatically be removed.")

                    embed = Embed(
                        title=f"Thanks for boosting {str(member.guild)}!", description=explain, color=self.bot.color)
                    embed.set_image(
                        url="https://cdn.discordapp.com/attachments/851689052112683008/851689105993236530/ezgif.com-optimize.gif")

                    await member.send(embed=embed)

        await self.role_management.assure_booster(member)
        try:
            await self.role_management.assure_role(member)
        except Exception:
            return

    @commands.Cog.listener()
    async def on_member_unboost(self, after):
        member = after
        await self.role_management.remove_role(member.guild, member, f"{after} (this custom role's primary user) stopped boosting")

    # Mod handlers

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if user.bot:
            return
        await self.role_management.remove_role(guild, user, f"{user} (this custom role's primary user) was banned")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        await self.role_management.remove_role(member.guild, member, f"{member} (this custom role's primary user) left")

    # Other handlers

    async def on_customizing_permit_removed(self, member):
        await self.role_management.remove_role(member.guild, member, f"{member} (this custom role's primary user) lost their customizing permit")


def setup(bot):
    bot.add_cog(RoleHandler(bot))
