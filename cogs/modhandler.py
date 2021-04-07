from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .utils.models import Booster


# This cog handles removing members (or ex-members) custom roles and booster row
class ModHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(self.bot.engine, class_=AsyncSession)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if user.bot:
            return
        async with self.sessionmaker() as session:
            async with session.begin():
                # get the booster
                result = await session.execute(select(Booster).where(Booster.user_id == user.id, Booster.guild_id == guild.id))
                booster = result.scalars().first()
                # get the role
                role = guild.get_role(booster.role_id)
                # delete that mf
                # TODO: If you implement role sharing, make sure you do whatever you need to do to the other user's booster row
                await role.delete(reason=f"{str(user)} (this custom role's primary user) was banned")
                # delete the booster row too
                await session.delete(booster)
            await session.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
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
                await role.delete(reason=f"{str(member)} (this custom role's primary user) left")
                # set the role id to none
                booster.role_id = None
            await session.commit()


def setup(bot):
    bot.add_cog(ModHandler(bot))
