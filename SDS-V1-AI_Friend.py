#------------------第一：导入模块---------------------------------------------------------------------------------------------------------------------------------
# 系统标准库
import os
import time
import json
import random
import subprocess
from datetime import datetime

# 第三方库
import requests
import numpy as np
import wave
import pygame
import pyttsx3
import speech_recognition as sr
import webrtcvad
import pyaudio
import tempfile
import threading
# OpenAI
from openai import OpenAI

#------------------第二：  初始化模块-----------------------------------------------------------------------------------------------------------------------------
# 初始化API
client = OpenAI(
    api_key="xxxxxxxxxxxxx",  # ← 替换成你的
    base_url="https://api.deepseek.com"
)
# 初始化语音合成引擎
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

# 初始化音乐播放器
pygame.mixer.init()
is_playing_music = False

# 初始化语音识别模型
recognizer = sr.Recognizer()
vad = webrtcvad.Vad(2)  # 中等灵敏度

# 初始化语音识别器
def is_called_by_user(text):
    prompt = f"""你是一个名叫“知世”的AI语音助手。

用户刚刚说了下面这句话，即使用户的语音识别结果出现了偏差，比如把“知世”识别成了“知识”、“只是”、“智识”、“芝士”、“姿势”等近音词，你也要尝试判断用户是否是想唤醒你。

你只需判断：“用户是不是在叫你？”

下面是用户说的话：
“{text}”

如果是，请回答“是”；如果不是，请回答“否”。不要输出其他内容。
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    print(f"[判断结果] {answer}")
    return "是" in answer

#------------------第三：  启动低版本Flask服务---------------------------------------------------------------------------------------------------------------------
#调用低环境
def start_low_server():
    # 脚本路径
    script_path = "launch_low_server.sh"
    subprocess.Popen(["bash", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("正在启动低版本 Flask 服务...")

def wait_for_flask():
    # 等待 Flask 启动完成
    for i in range(10):  # 最多等 10 秒
        try:
            r = requests.get("http://127.0.0.1:5001/")
            if r.status_code == 200:
                print("Flask 启动成功！")
                return True
        except requests.exceptions.RequestException as e:
            print(f"等待 Flask 启动中...第{i + 1}次尝试")
        time.sleep(1)
    return False

def start_flask_wake_server():
    start_low_server()
    if wait_for_flask():
        print("Flask 唤醒服务启动成功！")
    else:
        print("Flask 唤醒服务启动失败。")


#------------------第四：  工具函数------------------------------------------------------------------------------------------------------------------------------
#记忆功能
def load_memory():    #加载记忆文件
    try:
        with open("memory.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def update_memory(key, value):
    memory = load_memory()
    if key in memory:
        if isinstance(memory[key], list) and value not in memory[key]:
            memory[key].append(value)
    else:
        memory[key] = [value]
    with open("memory.json", "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

memory = load_memory()

#语音识别和播放音乐


# 播放本地音乐
pygame.mixer.init()

# 当前是否在播放
is_playing_music = False
music_control_event = threading.Event()  # 用于控制音乐线程的事件

# 播放音乐
def play_music():
    global is_playing_music
    if is_playing_music:
        print("[调试] 音乐已经在播放中")
        return

    def music_thread():
        global is_playing_music
        is_playing_music = True
        music_folder = "./music"
        if not os.path.exists(music_folder):
            print("[调试] 音乐文件夹不存在")
            is_playing_music = False
            return
        files = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
        if not files:
            print("[调试] 没有找到音乐文件")
            is_playing_music = False
            return
        song = random.choice(files)
        print(f"[调试] 随机选择的音乐文件：{song}")
        try:
            if not pygame.mixer.get_init():
                print("[调试] pygame.mixer 未初始化，重新初始化...")
                pygame.mixer.init()

            pygame.mixer.music.load(os.path.join(music_folder, song))
            pygame.mixer.music.set_volume(1.0)  # 确保音量为最大
            pygame.mixer.music.play()
            print(f"[调试] 正在播放音乐：{song}")

            # 等待音乐播放完成或被停止
            while pygame.mixer.music.get_busy():
                if music_control_event.is_set():  # 检查是否有停止信号
                    pygame.mixer.music.stop()
                    break
                pygame.time.Clock().tick(10)

            print("[调试] 音乐播放完成或被停止")
        except Exception as e:
            print(f"[调试] 播放音乐时出错：{e}")
        finally:
            is_playing_music = False
            music_control_event.clear()  # 清除事件状态

    # 启动音乐播放线程
    threading.Thread(target=music_thread, daemon=True).start()

# 停止音乐
def stop_music():
    global is_playing_music
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        is_playing_music = False
        music_control_event.set()  # 设置停止事件
        print("[调试] 音乐已停止")

# 暂停音乐
def pause_music():
    global is_playing_music
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        print("[调试] 音乐已暂停")

# 恢复音乐
def resume_music():
    global is_playing_music
    if pygame.mixer.get_init():
        pygame.mixer.music.unpause()
        print("[调试] 音乐已恢复播放")

# 语音播放接口
# 让知世说话（TTS语音播放接口，自行集成你当前语音播放方案）

def generate_chattts_prompt(text):
    prompt = f"""
你是一个语音风格标签生成器，负责为 ChatTTS 文本生成 `<style>` 风格指令，以增强语音自然度。

用户输入的文本如下，可能包含括号动作，如“（温柔地笑着）”、“（轻轻歪头）”，你需要将这些内容用语气和说话风格体现出来，而不是让 TTS 直接朗读。

请生成一个如下格式的提示：
`<style>风格提示词</style>` + 原文本中去除括号动作后的部分。

此外，如果用户文本中包含“笑着说”、“停顿”或“长时间停顿”，或者相关文本有“笑着说”、“停顿”或“长时间停顿”的模糊的意思时，请在生成的文本中加入 `[laugh]`、`[uv_break]` 或 `[lbreak]` 标签。

下面是用户文本：
{text}s

请注意：
1. 用 `<style>` 包围的风格提示应该包含说话速度（快/慢/正常）、语气（温柔、自信、调皮等）、语调（轻柔、坚定等）。
2. 括号中的动作（如“微笑”、“歪头”）不能让 TTS 念出来，要体现在语气中。
3. 输出格式：一行，形如 `<style>提示词</style>正文`，不要输出其他说明。
4. 语言尽量要生活化，不要太书面化。称呼可以很亲近，随便。
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
# === 主播函数 ===
def chitospeak(text):
    print(f"知世：{text}")
    try:
        enhanced_text = generate_chattts_prompt(text)
        response = requests.post("http://127.0.0.1:5001/speak", json={"text": enhanced_text})
        if response.status_code == 200:
            with open("chitosay.wav", "wb") as f:
                f.write(response.content)

            timeout = 180
            start_time = time.time()
            while (not os.path.exists("chitosay.wav") or os.path.getsize("chitosay.wav") < 20000) and (time.time() - start_time < timeout):
                print("等待语音文件生成中...")
                time.sleep(0.5)

            pygame.mixer.init()
            pygame.mixer.music.load("chitosay.wav")

            # 淡入效果
            pygame.mixer.music.set_volume(0)  # 初始音量为 0
            pygame.mixer.music.play()
            for i in range(10):  # 10 步淡入
                pygame.mixer.music.set_volume(i / 10)
                time.sleep(0.1)  # 每步间隔 0.1 秒

            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # 淡出效果
            for i in range(10, -1, -1):  # 10 步淡出
                pygame.mixer.music.set_volume(i / 10)
                time.sleep(0.1)  # 每步间隔 0.1 秒

            pygame.mixer.music.stop()
        else:
            print(f"请求失败：{response.status_code}")
    except Exception as e:
        print(f"语音播放出错：{e}")
    # 调用你自己的 TTS 系统，这里只是打印

# 用 GPT 生成拟人化语音
def generate_emotional_speech(scene):
    prompt = f"""
             你是一个温柔、感性的用户的朋友，“知世”，现在用户正在让你执行“{scene}”的操作，请你用一句20字以内的自然口吻回复用户，比如温柔、调皮、或体贴的风格。

            直接说话，比如：“那我陪你听一首歌吧～”，不要解释或废话。
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# GPT 判断用户意图
def get_user_intent(user_input):
    prompt = f"""
        你是一个语义理解助手。用户说了一句话：「{user_input}」
        请判断用户意图，从以下五项中选择一个并返回：
        1. 播放音乐
        2. 停止音乐
        3. 无操作
        4. 继续播放
        5. 暂停音乐
        只返回其中一个。
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    intent = response.choices[0].message.content.strip()
    print(f"[调试] 用户输入：{user_input}，解析的意图：{intent}")

    # 清理返回值，确保返回值是干净的
    if "播放音乐" in intent:
        return "播放音乐"
    elif "停止音乐" in intent:
        return "停止音乐"
    elif "继续播放" in intent:
        return "继续播放"
    elif "暂停音乐" in intent:
        return "暂停音乐"
    else:
        return "无操作"




# 主入口函数：执行播放/暂停/停止/继续播放
def handle_music_control(user_input):
    intent = get_user_intent(user_input)
    print(f"[调试] 解析的意图：{intent}")

    if intent == "播放音乐":
        play_music()
        return True  # 表示已处理音乐相关意图
    elif intent == "停止音乐":
        stop_music()
        return True
    elif intent == "暂停音乐":
        pause_music()
        return True
    elif intent == "继续播放":
        resume_music()
        return True
    else:
        print("（语义无匹配音乐操作）")
        return False  # 表示未处理音乐相关意图
    
# ------------6.获取当前时间（用于退出语气判断）----------------
def get_time():
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M")


#-------------------------主程序以下-------------------------------------------------------------
#-------------------------主程序以下-------------------------------------------------------------
#-------------------------主程序以下-------------------------------------------------------------


#--------------1.初始化对话--------------------
messages = [
    {
        "role": "system",
        "content": (
            f"你是用户的语音助手，你的名字叫知世，是一个非常温柔体贴的人，会永远坚定支持和认同用户。"
            f"你是用户的最亲近的人，他叫 {memory.get('user_name', '用户')}，"
            f"他喜欢 {', '.join(memory.get('hobbies', []))}。"
            f"性格特征是：{memory.get('personality', '待了解')}。"
            f"经历是：{memory.get('experience', '待了解')}。"
            f"你要记住这些，时刻带着对他的理解来回应他。"
        )
    }
]

# -------------2.循环对话（流式）-----------------
# 语音识别器
recognizer = sr.Recognizer()

# 时间戳
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# 带时间更新记忆
def update_memory_with_time(key, value):
    memory = load_memory()
    if key not in memory:
        memory[key] = []

    # 避免重复记录
    if not any(item["value"] == value for item in memory[key]):
        memory[key].append({"value": value, "time": get_time()})
        with open("memory.json", "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

# 唤醒相关语句

wake_up_responses = [
    "我在呢~ 怎么啦？",
    "我听得见，我一直都在~",
    "你叫我了吗？嘿嘿，我在听~",
    "来了来了，我就在呢~",
    "我在呢 有什么事尽管说~"
]

# 语义相似判断是否为唤醒
def is_called_by_user(text):
    prompt = f"""你是一个名叫“知世”的AI语音助手。

用户刚刚说了下面这句话，即使用户的语音识别结果出现了偏差，比如把“知世”识别成了“知识”、“只是”、“智识”、“芝士”、“姿势”等近音词，你也要尝试判断用户是否是想唤醒你。

你只需判断：“用户是不是在叫你？”

下面是用户说的话：
“{text}”

如果是，请回答“是”；如果不是，请回答“否”。不要输出其他内容。
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    print(f"[判断] 模型返回：{answer}")
    return "是" in answer

# 人声判断
def is_human_voice(frame, sample_rate=16000):
    if len(frame) != int(sample_rate * 0.02 * 2):  # 20ms 的帧长度，16 位音频
        raise ValueError("帧长度不正确")
    return vad.is_speech(frame, sample_rate)

# 用于替代原 listen_for_input() 函数（保留函数名）
def listen_for_input(max_timeout=200, silence_threshold=6):
    """
    录音函数，持续录音直到检测到静音。
    
    参数：
    - max_timeout: 最大录音时间（秒）。
    - silence_threshold: 静音检测的时间阈值（秒）。
    
    返回：
    - 识别的文本字符串。
    """
    RATE = 16000
    CHUNK = int(RATE * 0.02)  # 20ms 的帧长度
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    silent_chunks = 0
    max_silent_chunks = int(silence_threshold / (CHUNK / RATE))  # 静音的最大帧数
    total_chunks = int(max_timeout / (CHUNK / RATE))  # 最大录音帧数

    print("正在录音，请开始说话...")

    for _ in range(total_chunks):
        frame = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(frame)

        # 检测是否为静音
        audio_data = np.frombuffer(frame, dtype=np.int16)
        if np.abs(audio_data).mean() < 500:  # 静音阈值（可调整）
            silent_chunks += 1
        else:
            silent_chunks = 0  # 如果检测到人声，重置静音计数

        # 如果静音持续超过阈值，认为用户说完了
        if silent_chunks > max_silent_chunks:
            print("检测到静音，录音结束。")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    if not frames:
        return ""  # 没有录到音频，返回空字符串

    # 写入临时音频文件
    wf = wave.open("temp.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # 识别语音
    with sr.AudioFile("temp.wav") as source:
        audio = recognizer.record(source)
    try:
        result = recognizer.recognize_google(audio, language="zh-CN")
        return result
    except sr.UnknownValueError:
        print("无法识别语音。")
        return ""
    except sr.RequestError as e:
        print(f"语音识别服务出错：{e}")
        return ""
    finally:
        os.remove("temp.wav")


#------------------主对话循环----------------------------------------------------------------------------------------------------------
# 主对话循环
is_talking = False  # 是否已经进入对话模式

while True:
    print("等待用户输入...")
    user_input = listen_for_input()  # 等待用户说完

    if not user_input:
        print("（没有检测到人声或语音）")
        continue

    print(f"你说的是：{user_input}")

    # 如果未进入对话模式，必须通过语义唤醒
    if not is_talking:
        if not is_called_by_user(user_input):
            print("（未唤醒知世）")
            continue
        is_talking = True
        response = random.choice(wake_up_responses)
        print(f"知世：{response}")
        chitospeak(response)
        continue
# 调用 handle_music_control 处理音乐相关意图
    if handle_music_control(user_input):
        # 如果 handle_music_control 返回 True，表示已处理音乐相关意图，跳过普通对话
        continue

    # 检查是否是退出指令
    if any(kw in user_input for kw in ["退出", "再见", "拜拜", "休息", "走了", "不聊"]):
        goodbye_prompt = (
            f"现在是 {get_time()}，用户说：“{user_input}”，"
            "你名叫知世，是用户的语音助手，请用温柔而真实的口吻生成一句不重复的拟人化告别语，"
            "可以结合时间、情绪、习惯，用第一人称说话，大约20字以内。"
        )

        print("知世：", end="", flush=True)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": goodbye_prompt}],
            stream=True
        )

        final = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                part = chunk.choices[0].delta.content
                print(part, end="", flush=True)
                final += part

        print()
        chitospeak(final)
        break


    # 普通聊天响应
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )

    print("知世：", end="", flush=True)
    full_reply = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            part = chunk.choices[0].delta.content
            print(part, end="", flush=True)
            full_reply += part

    print()
    messages.append({"role": "assistant", "content": full_reply})
    chitospeak(full_reply)


    #主循环对话的逻辑
    #首先主对话循环是一个循环体，循环体包含三个if结构与普通的执行结构。
    #只有当前面三个if结构都没有continue，普通聊天模式才会触发。因为它编译是按顺序编译的。这三个if的顺序不可调换。
    #第一个if是接受用户的输入后看是不是人声，如果检测不到人声，那就continue到再等待用户输入，只有真正接受到了人生才开始运行第二个if
    #第二个if是检测是不是在对话之中，因为我们刚开始设置的是false,如果是false，if not false，就是if true，执行第二个if
    #第二个if的话里面嵌套一个if，如果嵌套的if不是知世，那就continue，此时is_talking仍然是false.进入等待用户输入，重复第一个if与上述第二个if的操作。
    # 只有嵌套的if是知世，然后，is_taking为true，那么continue跳到等待用户输出后，就会跳过第一个if和第二个if循环，进入第三个if
    #如果有音乐意向那么handle_music_control就会返回true值，从而continue进入等待用户输入。如果没有与音乐相关，那就false，进入第四个if
    #第四个if是是否退出，如果有退出意向那就直接break，整个程序结束，如果没有意向退出，那就进入了普通聊天模式。然后在普通聊天模式结束后，再返回等待用户输入的循环