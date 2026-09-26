"""下载运行所需的模型（宿主机或容器内执行一次即可）。

用法（在项目根目录）：
    python scripts/download_models.py
"""
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def download_piper():
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium"
    out = os.path.join(ROOT, "models", "piper")
    os.makedirs(out, exist_ok=True)
    for name in [
        "zh_CN-huayan-medium.onnx",
        "zh_CN-huayan-medium.onnx.json",
    ]:
        dest = os.path.join(out, name)
        if os.path.exists(dest):
            print(f"已存在，跳过：{dest}")
            continue
        url = f"{base}/{name}"
        print(f"下载：{url}")
        urllib.request.urlretrieve(url, dest)
    print("Piper 模型下载完成")


def download_whisper(model_size="small"):
    from faster_whisper import WhisperModel
    print(f"下载 faster-whisper 模型：{model_size}（首次会从 HuggingFace 拉取）")
    WhisperModel(model_size, device="cpu", compute_type="int8")
    print("faster-whisper 模型下载完成")


if __name__ == "__main__":
    download_piper()
    download_whisper(os.environ.get("WHISPER_MODEL", "small"))
