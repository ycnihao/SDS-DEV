import os
import sounddevice as sd
import numpy as np
import webrtcvad
from faster_whisper import WhisperModel

RATE = 16000
CHUNK = int(RATE * 0.02)
CHANNELS = 1
DTYPE = "int16"


vad = webrtcvad.Vad(2)

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cuda")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "float16")


def _load_whisper():
    try:
        return WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
    except Exception as e:
        print(f"[STT] 用 {WHISPER_DEVICE} 加载失败，回退 CPU：{e}")
        return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


model = _load_whisper()

def is_human_voice(frame,sample_rate=16000):
    return vad.is_speech(frame,sample_rate)

def listen_for_input(timeout=5):
    frames = []
    triggered = False
    silence_count = 0
    max_silence = int(1/0.02)

    def callback(indata,frame_out,time,status):
        nonlocal triggered,silence_count,frames
        frame_bytes = indata.tobytes()

        is_speech = False
        try:
            is_speech = is_human_voice(frame_bytes, 16000)
        except Exception as e:
            pass
        if not triggered:
            if is_speech:
                triggered = True
        
                frames.append(indata.copy())
        else:
            frames.append(indata.copy())
            if is_speech:
                silence_count = 0
            else:
                silence_count += 1
                if silence_count > max_silence:
                    raise sd.CallbackStop()
    try:
        with sd.InputStream(
            samplerate=RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=CHUNK,
            callback=callback,
        ):          
            sd.sleep(int(timeout*1000))
    except sd.CallbackStop:
        pass

    if not frames:
        return ""
    
    audio_np = np.concatenate(frames,axis=0)
    audio_np = audio_np.astype(np.float32) / 32768.0

    segments,_=model.transcribe(audio_np,language='zh')
    result = ''
    for seg in segments:
        result += seg.text

    return result.strip()
