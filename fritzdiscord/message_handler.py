import requests
import json
import sys

class handler():
    def __init__(self, token :str, sbot :bool = False) -> None:
        self.token = token
        self.sbot = sbot
        

    def get_token(self):
        # file = open("./token", "r")
        # token = file.read()
        # file.close()
        # return token
        return self.token


    def is_bot(self) -> bool:
        # return True
        return not self.sbot

    def get_headers(self, json :bool):
        headers = {"Authorization": self.is_bot() * "Bot " + self.get_token()}
        if json: headers["Content-type"] = "application/json"
        return headers

    def deserialize_json(self, text :str) -> "any|False":
        try:
            data = json.loads(text)
        except:
            print("Can't deserialize server response into json!", file=sys.stderr)
            return False
        return data

    def check_success(self, req):
        if not req.status_code in [200, 204]:
            print(f"Status code is {req.status_code} and response data is {req.text}!", file=sys.stderr)
            return False

    def send_message(self, message :str, channel_id :str, message_reference :tuple = ("0", "0"), reference_ping :bool = False, flags :int = 0, silent :bool = False):
        'Channel id is a string, if silent and flags is provided they are ored, else flags is 0 (silent is 1 << 12).'


        try:
            if message_reference[0] == "0" or message_reference[1] == "0":
                req = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", json={"content": message, "flags": flags | (silent * (1 << 12))}, headers=self.get_headers(True))
            else:
                req = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", json={"content": message,"message_reference": {"channel_id": message_reference[0],"message_id": message_reference[1]}, "replied_user": reference_ping, "flags": flags | (silent * (1 << 12))}, headers=self.get_token(True))


            if not self.check_success(req): return False
            data = self.deserialize_json(req.text)
            return data
        except Exception:
            return False


    def delete_message(self, channel_id :str, message_id :str) -> bool:
        'Both channel id and message id are strings.'


        try:
            req = requests.delete(f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}", headers=self.get_headers(False))

            if not self.check_success(req): return False
            return True
        except Exception:
            return False
