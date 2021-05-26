from discord import Color
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .utils.models import Booster
from .utils.errors import TooManyRoles


class RoleCommon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessionmaker = sessionmaker(
            self.bot.engine, class_=AsyncSession, future=True)

    async def assure_role(self, member):
        guild = member.guild
        # get a member object of our bot user
        bot = guild.get_member(self.bot.user.id)
        bot_top_role = bot.roles[-1]  # bot's top role

        if len(guild.roles) >= 249:
            raise TooManyRoles

        async with self.sessionmaker() as session:
            async with session.begin():
                result = await session.execute(select(Booster).where(Booster.user_id == member.id, Booster.guild_id == guild.id))
                booster = result.scalars().first()
                custom_role = guild.get_role(booster.role_id)

                visible_role = None

                # find the role that currently is showing for color
                for member_role in reversed(member.roles):
                    if member_role.color != Color.default():
                        visible_role = member_role
                        break
                
                # if there isn't a colored role just make the @everyone role it so that the next 2nd bit works
                if visible_role == None:
                    visible_role = guild.default_role
                
                # return the role if the role is already in the right spot
                if custom_role != None:
                    if visible_role == custom_role:
                        return custom_role

                # check to make sure the bot can make roles above the visible role
                if bot_top_role <= visible_role:
                    return # TODO: replace with a exception
                
                if custom_role == None:
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
                    booster.role_id = custom_role.id
                
                await custom_role.edit(position=visible_role.position+1)
                
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


def setup(bot):
    bot.add_cog(RoleCommon(bot))
