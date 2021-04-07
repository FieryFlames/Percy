from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .utils.models import Booster


# This cog handles boosting and unboosting
class BoostHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)
        self.role_management = self.bot.get_cog("RoleManagement")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # boost
        if not before.premium_since and after.premium_since:
            await self.on_member_boost(after)
        # stop boosting
        elif not after.premium_since and before.premium_since:
            await self.on_member_unboost(after)

    async def on_member_boost(self, member):
        await self.role_management.assure_booster(member)
        try:
            await self.role_management.assure_role(member)
        except Exception:
            return

    async def on_member_unboost(self, member):
        guild = member.guild
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == guild.id))
                booster = result.scalars().first()
                # get the role
                role = guild.get_role(booster.role_id)
                # delete that mf
                # TODO: If you implement role sharing, make sure you do whatever you need to do to the other user's booster row
                await role.delete(reason=f"{str(member)} (this custom role's primary user) stopped boosting")
                # update booster
                booster.role_id = None
            await session.commit()


def setup(bot):
    bot.add_cog(BoostHandler(bot))
