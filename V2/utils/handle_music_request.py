from utils.AI_related_function import get_user_intent
def handle_music_request(user_input): #先占位，后画再写音乐逻辑
    intent = get_user_intent(user_input)
    if intent == "播放音乐":
        play_music()
        return True
    elif intent == "暂停音乐":
        pause_music()
        return True
    elif intent == "停止音乐":
        stop_music()
        return True
    elif intent == "继续播放音乐":
        resume_music()
        return True
    elif intent == "下一首":
        next_music()
        return True
    elif intent == "上一首":
        previous_music()
        return True
    else:
        print("没有识别到音乐相关的意图")
        return False
def play_music():  #先占位，后画再写音乐逻辑
    print("正在播放音乐...")
def pause_music():
    print("正在暂停音乐...")                
def stop_music():
    print("正在停止音乐...")        
def resume_music():
    print("正在继续播放音乐...")
def next_music():       
    print("正在播放下一首音乐...")
def previous_music():
    print("正在播放上一首音乐...")
