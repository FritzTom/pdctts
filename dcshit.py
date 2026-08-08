
from tempfile import NamedTemporaryFile
from faster_whisper import WhisperModel
from fritzdiscord import anything, send_long_message
from dotenv import load_dotenv
from os import environ, unlink
import threading
import requests
import vc

load_dotenv()

model_size = "large-v3-turbo"
print("creating model...")
model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("done.")
bot = anything.bot(environ["TOKEN"], log_messages=False)

"""
commands:
{"id":"1535545539536486492","application_id":"1532865100816318676","version":"1535556724587503656","default_member_permissions":null,"type":3,"name":"transcribe","name_localizations":null,"description":"","description_localizations":null,"dm_permission":false,"contexts":[0,2],"integration_types":[0,1],"nsfw":false}


"""

@bot.bot_ready_decorator
def ready(self):
    self.send_json_request({
        "op": 4,
        "d": {
            "guild_id": "1391527917518848144",
            "channel_id": "1391537542637158451",
            "self_mute": True,
            "self_deaf": True
        }
    })

@bot.decorator_wrapper(type="VOICE_SERVER_UPDATE")
def voice_server_update(self, event):
    data = event["data"]
    token = data["token"]
    endpoint = data["endpoint"]
    guild_id = data["guild_id"]
    vc.handle_data(environ["APPLICATION_ID"], None, token, endpoint, guild_id)
    return True

@bot.decorator_wrapper(type="VOICE_STATE_UPDATE")
def voice_state_update(self, event):
    data = event["data"]
    if data["user_id"] != environ["APPLICATION_ID"]: return False
    vc.handle_data(data["user_id"], data["session_id"], None, None, data.get("guild_id"))
    return True

def transcribe(token, url):
    print("downloading audio...")
    res = requests.get(url)
    if not res.ok:
        requests.patch(f"https://discord.com/api/v9/webhooks/{environ['APPLICATION_ID']}/{token}/messages/@original",
                       json={"content": "Failed to create transcription."})
        return
    af = res.content
    print("done.")
    f = NamedTemporaryFile(mode="wb", delete=False)
    f.write(af)
    f.close()
    segments, info = model.transcribe(f.name, beam_size=8, vad_filter=True)
    print("transcribing...")
    segments = list(segments)
    print("done.")
    unlink(f.name)
    text = ''.join([i.text for i in segments])
    if len(text) < 2000:
        requests.patch(f"https://discord.com/api/v9/webhooks/{environ['APPLICATION_ID']}/{token}/messages/@original",
                           json={"content": text})
    else:
        ct, msg = send_long_message.make_long_message(text)
        requests.patch(f"https://discord.com/api/v9/webhooks/{environ['APPLICATION_ID']}/{token}/messages/@original",
                       headers={"Content-type": ct}, data=msg)

@bot.decorator_wrapper(type="INTERACTION_CREATE")
def interaction_create(self, event):
    data = event["data"]
    token = data["token"]
    iid = data["id"]
    requests.post(f"https://discord.com/api/v9/interactions/{iid}/{token}/callback", json={"type": 5, "data": {"flags": 1 << 6}})
    msgs = list(data["data"]["resolved"]["messages"].values())
    msg = msgs[0]
    done = False
    while not done:
        if len(msg["attachments"]) < 1:
            break
        am = msg["attachments"][0]
        if "duration_secs" not in am:
            break
        if am["duration_secs"] > (60.0 * 5):
            break
        if "content_type" not in am:
            break
        if am["content_type"] != "audio/ogg":
            break
        if am["size"] > 2_000_000:
            break
        url = am["proxy_url"]
        thread = threading.Thread(target=transcribe, args=(token, url))
        thread.daemon = True
        thread.start()
        return True
    requests.patch(f"https://discord.com/api/v9/webhooks/{environ['APPLICATION_ID']}/{token}/messages/@original",
                  json={"content": "Failed to create transcription."})
    return True

if __name__ == "__main__": bot.main()
