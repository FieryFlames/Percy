from discord import Color
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .utils.models import Booster
from .utils.errors import BelowMember, TooManyRoles


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


def setup(bot):
    bot.add_cog(RoleCommon(bot))
