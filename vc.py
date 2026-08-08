
import websocket
import threading
import socket
import random
import time
import json

STATE = {}

def handle_data(user_id, session_id, token, endpoint, guild_id):
    data = {"user_id": user_id, "session_id": session_id, "token": token, "endpoint": endpoint, "guild_id": guild_id}
    if data["guild_id"] is not None:
        if STATE["guild_id"] is not None:
            if data["guild_id"] != STATE["guild_id"]:
                clear_state()
    for k,v in data.items():
        if v is not None: STATE[k] = v

    if all([i is not None for i in STATE.values()]):
        thread = threading.Thread(target=handle_voice)
        thread.daemon = True
        thread.start()

def clear_state():
    STATE.update({"user_id": None, "session_id": None, "token": None, "endpoint": None, "guild_id": None})
clear_state()

def handle_voice():
    sc = STATE.copy()
    user_id, session_id, token, endpoint, guild_id = list(sc.values())
    print(f"Starting voice session: {sc}")
    ws = websocket.WebSocket()
    ws.connect(f"wss://{endpoint}/?v=8")
    ws.send(json.dumps({
        "op": 0,
        "d": {
            "server_id": guild_id,
            "user_id": user_id,
            "session_id": session_id,
            "token": token,
            "max_dave_protocol_version": 0
        }
    }))

    hi = -1
    ni = -1
    ls = -1
    ssrc = None
    ip = None
    port = None
    modes = None
    voice_thread = None
    while True:
        d = [False]
        thread = threading.Thread(target=lambda x, nt, w: [time.sleep(max(nt, 1)), w.abort() if not x[0] else None], args=(d, ni - time.time(), ws))
        thread.daemon = True
        thread.start()
        try:
            rd = ws.recv()
            d[0] = True
        except Exception as err:
            print(repr(err))
            data = None
        else:
            data = json.loads(rd)
        if time.time() >= ni:
            ni = time.time() + hi
            send_heartbeat(ws, ls)
        if data is None: continue
        if "seq" in data: ls = data["seq"]
        match data["op"]:
            case 8:
                hi = data["d"]["heartbeat_interval"] / 1000
                print(f"{hi=}")
                ni = time.time() + hi
                send_heartbeat(ws, ls)
            case 6:
                pass
            case 2:
                ssrc = data["d"]["ssrc"]
                ip = data["d"]["ip"]
                port = data["d"]["port"]
                modes = data["d"]["modes"]
                print("Got data, connecting to UDP socket.")
                print(f"{ssrc=};{ip=};{port=};{modes=}")
                voice_thread = threading.Thread(target=handle_udp, args=(ws, ssrc, ip, port, modes))
                voice_thread.daemon = True
                voice_thread.start()
            case _:
                print(f"Unknown event: {data}")

def send_heartbeat(ws, ls):
    ws.send(json.dumps({
        "op": 3,
        "d": {
            "t": int(time.time()) + random.randint(-2, 2),
            "seq_ack": ls
        }
    }))

def handle_udp(ws, ssrc :int, ip, port, modes):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    print(f"Using UDP over {ip}:{port}")
    addr = ip, port
    while True:
        s.sendto(b"\x00\x01\x00\x46" + ssrc.to_bytes(4, "big", signed=False) + b"\x00" * 66, addr)
        try:
            data, raddr = s.recvfrom(512)
        except Exception:
            continue
        print(data, raddr)
        if len(data) != 74:
            continue
        data = data[8:]
        se = data.index(b"\x00")
        sip = data[:se].decode("utf-8")
        data = data[se:]
        sport = int.from_bytes(data[-2:], "big", signed=False)
        break
    print(f"{sip=};{sport=};")
    ws.send(json.dumps({
        "op": 1,
        "d": {
            "protocol": "udp",
            "data": {
                "address": sip,
                "port": sport,
                "mode": "aead_xchacha20_poly1305_rtpsize"
            }
        }
    }))

