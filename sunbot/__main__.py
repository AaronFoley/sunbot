import os
from sunbot.bot import Sunbot

if os.name != "nt":
    import uvloop
    uvloop.install()

if __name__ == "__main__":
    bot = Sunbot()
    bot.run()
