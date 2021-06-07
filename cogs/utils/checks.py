import discord
from discord.ext import commands
from discord.ext.commands.errors import BotMissingPermissions, NoPrivateMessage

from .errors import NotAllowedRole, NotBoosting


def is_allowed_role():
    async def predicate(ctx):
        member = ctx.author
        # firstly check if they are blocked from having a custom role. this takes priority
        for role in member.roles:
            if role.name.lower() == "cease customizing":
                raise NotAllowedRole

        # Now, check if they're allowed a custom role
        for role in member.roles:
            if role.name.lower().startswith("customizing permit"):
                return True

        # Finally, check if they're boosting
        if member.premium_since != None:
            return True
        else:
            raise NotBoosting
    return commands.check(predicate)

# Modified discord.py check to work with slash commands
def bot_has_guild_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(ctx):
        if not ctx.guild:
            raise NoPrivateMessage

        permissions = ctx.guild.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return commands.check(predicate)
