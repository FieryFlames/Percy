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
        self.role_management = self.bot.get_cog("RoleManagement")

    async def remove_role(self, guild, user, reason):
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == user.id, Booster.guild_id == guild.id))
                booster = result.scalars().first()
                if not booster:
                    return
                # get the role
                role = guild.get_role(booster.role_id)
                # delete that mf
                if role != None:
                    await role.delete(reason=reason.format(user=user))
                # delete the booster row too
                await session.delete(booster)
            await session.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        print("here")
        # boost
        if not before.premium_since and after.premium_since:
            await self.on_member_boost(after)
            return
        # stop boosting
        elif not after.premium_since and before.premium_since:
            await self.on_member_unboost(after)
            return
        # permit for customizing removed
        had_permit = False
        has_permit = False
        for role in before.roles:
            if role.name.lower().startswith("customizing permit"):
                had_permit = True
        for role in after.roles:
            if role.name.lower().startswith("customizing permit"):
                has_permit = True
        
        if has_permit == False and had_permit == True:
            await self.on_customizing_permit_removed(after)
    # Boost handlers

    async def on_member_boost(self, member):
        await self.role_management.assure_booster(member)
        try:
            await self.role_management.assure_role(member)
        except Exception:
            return

    async def on_member_unboost(self, member):
        await self.remove_role(member.guild, member, "{user} (this custom role's primary user) stopped boosting")

    # Mod handlers

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if user.bot:
            return
        await self.remove_role(guild, user, "{user} (this custom role's primary user) was banned")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        await self.remove_role(member.guild, member, "{user} (this custom role's primary user) left")

    # Other handlers

    async def on_customizing_permit_removed(self, member):
        await self.remove_role(member.guild, member, "{user} (this custom role's primary user) lost their customizing permit")


def setup(bot):
    bot.add_cog(RoleHandler(bot))
