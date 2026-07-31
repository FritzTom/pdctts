
from fritzdiscord import anything
from dotenv import load_dotenv
from os import environ
import socket
load_dotenv()

bot = anything.bot(environ["TOKEN"], log_messages=False)

bot.main()
