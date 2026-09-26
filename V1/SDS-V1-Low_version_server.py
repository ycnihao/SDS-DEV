from flask import Flask, request, send_file
import torch
import sys
import os
import tempfile
import numpy as np
import soundfile as sf
import re

# 设置 ChatTTS 路径
chattts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ChatTTS'))
sys.path.insert(0, chattts_root)

from tools.logger import get_logger
from tools.normalizer.zh import normalizer_zh_tn
import ChatTTS

logger = get_logger("FlaskApp")
chat = ChatTTS.Chat(logger)
 
# 注册中文正规化（英文的可以略过）
try:
    chat.normalizer.register("zh", normalizer_zh_tn())
except:
    pass

# 加载模型
chat.load(source="huggingface")


# 全局变量：固定女性音色（从.pt文件加载）

embedding_path = "/voice/就你了.pt"
fixed_spk_emb = torch.load(embedding_path, map_location="cpu")

app = Flask(__name__)

def parse_style_and_text(text):
    """提取 <style>风格</style>文本 的结构"""
    match = re.match(r"<style>(.*?)</style>(.*)", text.strip(), re.DOTALL)
    if match:
        style_str = match.group(1).strip()
        main_text = match.group(2).strip()
        return style_str, main_text
    else:
        return "", text.strip()

def style_to_params(style_str):
    """将风格关键词映射为 ChatTTS 推理参数"""
    speed = 1.0
    temperature = 0.3
    top_P = 0.7

    if "慢" in style_str:
        speed = 0.8
    elif "快" in style_str:
        speed = 1.2

    if "温柔" in style_str or "轻柔" in style_str:
        temperature = 0.2
        top_P = 0.6
    elif "坚定" in style_str or "自信" in style_str:
        temperature = 0.5
        top_P = 0.9
    elif "调皮" in style_str or "活泼" in style_str:
        temperature = 0.6
        top_P = 1.0
    elif "伤心" in style_str:
        temperature = 0.4
        top_P = 0.6

    return speed, temperature, top_P

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return {"error": "No text provided"}, 400

    # 提取 style 标签和正文
    style_str, clean_text = parse_style_and_text(text)

    # 映射 style 成为语音参数
    speed, temperature, top_P = style_to_params(style_str)

    # 构造推理参数
    params = ChatTTS.Chat.InferCodeParams()
    params.spk_emb = fixed_spk_emb
    params.speed = speed
    params.temperature = temperature
    params.top_P = top_P

    # 增加 RefineTextParams 支持笑声和停顿
    refine_params = ChatTTS.Chat.RefineTextParams(
        prompt="[oral_2][laugh_0][uv_break][lbreak]"  # 支持多种控制单元
    )


    wavs = chat.infer(
        text=[clean_text],
        params_infer_code=params,
        use_decoder=False,
        skip_refine_text=True,
        stream=False,
    )

    # 转成 numpy
    if isinstance(wavs[0], torch.Tensor):
        audio = wavs[0].squeeze().cpu().numpy()
    else:
        audio = wavs[0].squeeze()

    # 保存为临时 wav 文件返回
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio, samplerate=24000)
        temp_path = f.name
        return send_file(temp_path, mimetype="audio/wav")

if __name__ == '__main__':
    app.run(port=5001)