
from fritzdiscord import anything
import time

time_millis = lambda: int(1000 * time.time())


bot = anything.bot(sbot=True, compression=True, log_messages=False)


# @bot.bot_ready_decorator
def test(self : anything.bot):
    self.send_json_request({
        "op": 3,
        "d": {
            "since": None,
            "activities": [
                {
                    "name": "test",
                    "created_at": time.time() - 100
                }
            ],
            "status": "online",
            "afk": False
        }
    })

# @bot.decorator_wrapper(type="PRESENCE_UPDATE")
# def a(self :anything.bot, event):
#     print(event)

@bot.decorator_wrapper(type="USER_SETTINGS_PROTO_UPDATE")
def b(self : anything.bot, event):
    print(event["data"])


bot.start()

print("Press enter to stop the bot.")
input()
print("Stopping...")

bot.stop()
