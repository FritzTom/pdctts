
import websocket
import threading
import random
import json
import time
import zlib
import sys


class bot:
    def __init__(self, token :str = "", sbot :bool = False, compression :bool = False, safe_token :bool = False, log_messages :bool = True) -> None:
        self.hello_event = None
        self.last_sequence_number = None
        self.heartbeat_thread = None
        self.heartbeat_interval = None
        self.ws = None
        self.event_data = None
        self.input_thread = None
        self.connected = False
        self.normal_disconnect = None
        self.event = None
        self.pending_heartbeat_ack = None
        self.token = token
        self.debug = False
        self.log_unhandled = True
        self.bot_code = []
        self.bot_ready_callbacks = []
        self.sbot = sbot
        self.log_messages = log_messages
        self.transport_compression = compression
        self.decompressobj = None
        if self.transport_compression: self.decompressobj = zlib.decompressobj()

        if self.token == "":
            file = open("token", "r")
            self.token = file.read().replace("\n", "").replace("\r", "")
            file.close()
        elif safe_token:
            file = open("token", "w")
            file.write(self.token)
            file.close()
    
    def get_message_handler(self): return __import__("fritzdiscord.message_handler").message_handler.handler(self.token, self.sbot)
    

    def decorator_wrapper(self, op :int = 0, type :str = ""):
        self.decorator_op = op
        self.decorator_type = type
        def decorator(f):
            self.bot_code.append({"op": self.decorator_op, "type": self.decorator_type, "func": f})
        return decorator
    
    def bot_ready_decorator(self, f):
        self.bot_ready_callbacks.append(f)



    def recieve_json_response(self):
        attempts = 0
        buffer = b""
        while True:
            data = self.ws.recv()
            if not self.transport_compression:
                if data:
                    try:
                        json_data = json.loads(data)
                        return json_data
                    except Exception:
                        break
                if attempts >= 5: break
                time.sleep(1)
                attempts += 1
            else:
                buffer += data
                if data.endswith(b'\x00\x00\xff\xff'):
                    data = self.decompressobj.decompress(buffer)
                    buffer = b""
                    try:
                        json_data = json.loads(data)
                        return json_data
                    except Exception:
                        break
        return False

    def send_json_request(self, data) -> bool:
        try:
            self.ws.send(json.dumps(data))
        except Exception:
            return False
        return True

    def send_heartbeats(self) -> None:
        time.sleep((self.heartbeat_interval * random.random()) / 1000)
        self.pending_heartbeat_ack = True
        self.send_json_request({"op": 1, "d": self.last_sequence_number})
        while self.connected:
            while self.wait:
                pass
            time.sleep(self.heartbeat_interval / 1000)
            if self.pending_heartbeat_ack:
                print("Didn't recieve heartbeat ack, disconnecting!")
                self.normal_disconnect = 1
                self.connected = False
            self.pending_heartbeat_ack = True
            self.send_json_request({"op": 1, "d": self.last_sequence_number})

    def client_input(self):
        while self.connected:
            print("$ ", end="")
            sys.stdout.flush()
            cmd = ""
            char = ""
            while char != "\n":
                cmd = cmd + char
                char = sys.stdin.read(1)
            if cmd == "exit":
                self.connected = False
            if cmd == "help":
                print(self.help_message)
            if cmd.startswith("eval "):
                eval(cmd[5:])
            if cmd == "reconnect":
                pass
                # reconnect()
            if cmd == "bot":
                self.bot_active = True


    def main(self):
        '''Call this if you want to start the bot in the current thread, this is a blocking call.'''

        self.help_message = """

        ------------------------

        exit         --- Close the tcp socket and close the programm.

        help         --- Show this help.

        eval command --- execute a command / evaluate a expression.

        reconncet    --- reconnect using session id and reconnect gateway url. DONT USE BROKEN -- work in progress

        bot          --- run bot.

        ------------------------
        """



        self.last_sequence_number = None
        self.pending_heartbeat_ack = False

        self.ws = websocket.WebSocket()
        self.ws.connect("wss://gateway.discord.gg/?v=10&encoding=json" + "&compress=zlib-stream" * self.transport_compression)
        self.hello_event = self.recieve_json_response()
        print(self.hello_event)
        self.heartbeat_interval = self.hello_event["d"]["heartbeat_interval"]

        self.connected = True
        self.wait = False
        self.bot_active = False

        self.heartbeat_thread = threading.Thread(target=self.send_heartbeats)
        self.heartbeat_thread.start()

        if not self.sbot:
            identify_data = {
              "token": self.token,
              "intents": 1 << 9 | 1 << 15 | 1 << 12 | 1 << 7,
              "properties": {
                "os": "linux",
                "browser": "Fitzie_Ficies",
                "device": "Fitzie_Ficies"
              }
            }
        else:
            identify_data = {
              "token": self.token,
              "capabilities": 16381,
              "properties": {
                "os": "Linux",
                "browser": "Firefox",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
                "browser_version": "119.0",
                "os_version": "",
                "referrer": "https://discord.com/",
                "referring_domain": "discord.com",
                "referrer_current": "",
                "referring_domain_current": "",
                "release_channel": "stable",
                "client_build_number":247232,
                "client_event_source":None
              },
              "presence": {
                "status": "online",
                "since": 0,
                "activities": [],
                "afk": False
              },
              "compress": False,
              "client_state": {
                "guild_versions": {},
                "highest_last_message_id": "0",
                "read_state_version": 0,
                "user_guild_settings_version": -1,
                "user_settings_version": -1,
                "private_channels_version": "0",
                "api_code_version": 0
              }
            }


        self.send_json_request({"op": 2, "d": identify_data})
        
        self.event = None
        self.event = self.recieve_json_response()
        while not self.event:
            self.event = self.recieve_json_response()

        self.ready_event = self.event
        print(f'Session id: {self.ready_event["d"]["session_id"]}\nResume gateway url: {self.ready_event["d"]["resume_gateway_url"]}')

        if self.debug:
            file = open("ready_event", "w")
            file.write(str(self.ready_event))
            file.close()


        self.normal_disconnect = 0
        self.do_reconnect = False


        if self.debug:
            self.input_thread = threading.Thread(target=self.client_input)
            self.input_thread.daemon = True
            self.input_thread.start()
        else:
            self.bot_active = True


        # file = open(3, "wb", buffering=0)
        class file:
            @staticmethod
            def write(data :bytes): print(data.decode("utf-8"), end="")
            @staticmethod
            def close(): pass


        if self.bot_active:
            for i in self.bot_ready_callbacks:
                try:
                    i(self)
                except Exception as err:
                    if self.debug: print(f"Fail in bot ready callback code.\nThis is a bug in user code so don't report this.\nError: {err}", file=sys.stderr)

        while True:
            while self.connected:
                while self.wait:
                    pass
                self.event = self.recieve_json_response()
                while not self.event:
                    self.event = self.recieve_json_response()

                try:
                    self.event_data = self.event["d"]
                except Exception:
                    self.event_data = None

                unknown_event = True

                try:
                    self.op = self.event["op"]
                except:
                    print("Recieved malformed packet without opcode.", file=sys.stderr)
                    self.op = None


                if self.op == 1:
                    unknown_event = False
                    self.send_json_request({"op": 1, "d": self.last_sequence_number})

                if self.op == 11:
                    unknown_event = False
                    if self.pending_heartbeat_ack:
                        self.pending_heartbeat_ack = False
                    else:
                        print("Recieved heartbeat ack even tho we didn't send heartbeat, disconnecting!")
                        self.connected = False

                if self.op == 0:
                    try:
                        if self.event["s"] != None:
                            self.last_sequence_number = self.event["s"]
                    except Exception:
                        pass
                    try:
                        self.dispatch_type = self.event["t"]
                    except Exception:
                        self.dispatch_type = None



                    if self.dispatch_type == "MESSAGE_CREATE":
                        if self.log_messages:
                            unknown_event = False
                            try:
                                for i in range(len(self.ready_event["d"]["guilds"])):
                                    if self.ready_event["d"]["guilds"][i]["id"] == self.event_data["guild_id"]:
                                        if not self.sbot:
                                            file.write(f'At {self.event_data["timestamp"]} in {self.ready_event["d"]["guilds"][i]["name"]}, {self.event_data["author"]["username"]}: {self.event_data["content"]}\n'.encode("utf-8"))
                                        else:
                                            file.write(f'At {self.event_data["timestamp"]} in {self.ready_event["d"]["guilds"][i]["properties"]["name"]}, {self.event_data["author"]["username"]}: {self.event_data["content"]}\n'.encode("utf-8"))
                            except Exception:
                                file.write(f'At {self.event_data["timestamp"]}, {self.event_data["author"]["username"]} said: {self.event_data["content"]}\n'.encode("utf-8"))

                if self.op == 7:
                    self.do_reconnect = True
                    self.connected = False
                    pass
                if self.do_reconnect: break

                if self.op == 9:
                    print("Invalid session.")
                    print("Event: " + str(self.event_data))
                    self.do_reconnect = False
                    break

                if self.bot_active:
                    for i in range(len(self.bot_code)):
                        if not (self.bot_code[i]["op"] == self.op and self.bot_code[i]["type"] in ["", self.dispatch_type]): continue
                        try:
                            if self.bot_code[i]["func"](self, {"op": self.op, "data": self.event_data, "type": self.dispatch_type, "event": self.event}):
                                unknown_event = False
                        except Exception as err:
                            if self.debug: print(f"Fail in bot code.\nThis is a bug in user code so don't report this.\nError: {err}", file=sys.stderr)


                if self.log_unhandled and unknown_event and not self.debug: print(f"Recieved unknowen event! Event was: {str(self.event)}", file=sys.stderr)
                if self.debug: print(f"DEBUG MODE --- Event: {str(self.event)}", file=sys.stderr)
            print("Disconnecting", file=sys.stderr)
            if not self.do_reconnect: break
            print("Reconnecting", file=sys.stderr)
            self.do_reconnect = False
            self.ws.close()
            self.connected = False
            self.heartbeat_thread.join()
            if self.sbot: continue
            self.ws = websocket.WebSocket()
            self.ws.connect(self.ready_event["d"]["resume_gateway_url"])
            self.heartbeat_interval = self.recieve_json_response()["d"]["heartbeat_interval"]
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeats)
            self.heartbeat_thread.start()
            self.send_json_request({
              "op": 6,
              "d": {
                "token": self.token,
                "session_id": self.ready_event["d"]["session_id"],
                "seq": self.last_sequence_number
              }
            })


        print("Exiting", file=sys.stderr)

        file.close()

        self.heartbeat_thread.join()

        try:
            if self.normal_disconnect == 0:
                self.ws.close(1000)
            elif self.normal_disconnect == 1:
                self.ws.close(1002)
        except OSError as err:
            if err.errno != 9:
                raise err


    def start(self):
        """Start the bot in a new thread you can use stop function to stop the bot."""

        self.most_important = threading.Thread(target=self.main)
        self.most_important.start()
        return

    def stop(self):
        """Stop the bot, only use this in combination with start function.
        Will wait until the bot has stopped."""
        
        self.connected = False
        self.most_important.join()
