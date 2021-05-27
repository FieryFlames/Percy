# Percy
Percy is a Discord bot that gives your server's boosters (& members) their own customizable roles, that can be customized with a command.

# Running locally
**⚠️ No support will be provided for running Percy locally.**

1. Download this repository.
2. Set up a database that is compatible with asyncronous SQLAlchemy.
3. Create a file containing the configuration data:
```toml
[Discord]
Token = "<token here>"

[SQLAlchemy]
URL = "<sqlalchemy url here>"

[Bot]
Cogs = ["cogs.role_commands", "cogs.role_common", "cogs.role_handler"]
Color = 0x<hex code>

[Emoji]
Yes = "+"
Warn = "/!\\"
No = "X"
Neutral = "/"
```
4. Now, run the bot with `python bot.py --config <config file>`