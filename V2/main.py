from utils.Chat_context import get_initial_messages
from utils.Speech_input import listen_for_input
from utils.AI_related_function import wake_up_responses,is_called_by_user,get_answer,goodbye_responses
from utils.Speech_output import speak_text
from utils.handle_music_request import handle_music_request

messages = get_initial_messages()
is_talking = False

while True:
    user_input = listen_for_input()
    print(f"你说的是：{user_input}")

    if not user_input:
        continue

    if not is_talking:
        if not is_called_by_user(user_input):
            print("你没有唤醒知世")
            continue
        is_talking = True
        response = wake_up_responses()
        print("知世：" + response)
        speak_text(response)
        user_input = user_input.strip()
    else:
        user_input = user_input.strip()
    print(f"\n 你说: {user_input}")

    if handle_music_request(user_input):
        continue
    messages.append({"role":"user","content":user_input})
    answer = get_answer(messages)
    
    messages.append({"role":"assistant","content":answer})

    speak_text(answer)
    
    print(f"知世: {answer}")

    if goodbye_responses(user_input):
        is_talking = False
    else:
        is_talking = True
