
from fritzdiscord import anything
from dotenv import load_dotenv
from os import environ
import socket
load_dotenv()

bot = anything.bot(environ["TOKEN"], log_messages=False)

@bot.bot_ready_decorator
def ready(self):
    self.send_json_request({
        "op": 4,
        "d": {
            "guild_id": "1391527917518848144",
            "channel_id": "1391527918689194138",
            "self_mute": True,
            "self_deaf": True
        }
    })

@bot.decorator_wrapper(type="VOICE_SERVER_UPDATE")
def voice_server_update(self, event):
    token = event["data"]["token"]
    endpoint = event["data"]["endpoint"]
    print(token, endpoint)
    return True

bot.main()
