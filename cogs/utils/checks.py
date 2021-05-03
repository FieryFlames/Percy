from discord.ext import commands
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
