import os
import queue
import threading
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from utils.AI_related_function import optimize_speech_text

PIPER_MODEL_PATH = os.environ.get(
    "PIPER_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "piper", "zh_CN-huayan-medium.onnx"),
)

_voice = None
_audio_queue = queue.Queue()


def get_voice():
    global _voice
    if _voice is None:
        print(f"[TTS] 加载 Piper 模型：{PIPER_MODEL_PATH}")
        _voice = PiperVoice.load(PIPER_MODEL_PATH)
    return _voice


def _player_thread(sample_rate):
    while True:
        chunk = _audio_queue.get()
        if chunk is None:
            break
        sd.play(chunk, sample_rate)
        sd.wait()


def speak_text(text):
    try:
        speech_text = optimize_speech_text(text)
        print(f"开始流式播放：{speech_text}")

        voice = get_voice()
        sample_rate = voice.config.sample_rate

        player = threading.Thread(target=_player_thread, args=(sample_rate,), daemon=True)
        player.start()

        for audio_bytes in voice.synthesize_stream_raw(speech_text):
            if not audio_bytes:
                continue
            pcm = np.frombuffer(audio_bytes, dtype=np.int16)
            _audio_queue.put(pcm)

        _audio_queue.put(None)
        player.join()
        print("播放完成")
    except Exception as e:
        print(f"播放出错了?{e}")
        _audio_queue.put(None)
