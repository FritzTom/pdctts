
from piper import PiperVoice
from pyaudio import PyAudio as pyaudio

PyAudio = pyaudio()

def main():
    voice = PiperVoice.load("./en_US-ryan-high.onnx")
    device = get_device()
    # while True:
    #     device.write(random.randbytes(100000))
    while True:
        for chunk in voice.synthesize("the quick brown fox jumps over the lazy dog."):
            # print(chunk)
            # print(chunk.audio_int16_bytes)
            # break
            data = chunk.audio_int16_bytes
            ndata = b""
            for i in range(len(data) >> 1):
                ndata += data[2 * i:2 * (i + 1)] * 2
            device.write(ndata)

        # break

def get_device():
    count = PyAudio.get_device_count()
    devices = [PyAudio.get_device_info_by_index(i) for i in range(count)]
    for i,v in enumerate(devices): v["li"] = i
    devices = [i for i in devices if i["maxOutputChannels"] > 0]
    default = [i for i in devices if i["name"] == "pulse"]
    if len(default) > 0: choice = default[0]["li"]
    choice = devices[ask_device(devices)]["li"]
    return PyAudio.open(44000, 1, PyAudio.get_format_from_width(2, True), False, True, None, choice)

def ask_device(devices):
    print('\n'.join([f"{i + 1}: {v['name']}" for i,v in enumerate(devices)]))
    while True:
        ct = input("> ")
        try:
            choice = int(ct)
        except ValueError:
            continue
        choice -= 1
        if choice < 0: continue
        if choice >= len(devices): continue
        return choice

if __name__ == "__main__": main()
