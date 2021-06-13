from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # boost
        if not before.premium_since and after.premium_since:
            self.bot.dispatch('member_boost', after)

        # stop boosting
        elif not after.premium_since and before.premium_since:
            self.bot.dispatch('member_unboost', after)


def setup(bot):
    bot.add_cog(Events(bot))
