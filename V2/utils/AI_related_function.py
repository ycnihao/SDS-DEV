import random
from clients.LLM_API import LLMClient

_LLM_client = None
def get_LLM_client():
    global _LLM_client
    if _LLM_client is None:
        _LLM_client = LLMClient()
        print(f"[AI服务商信息]初始化LLM,默认提供商：{_LLM_client.active_provider}")
    return  _LLM_client

def wake_up_responses():
    wake_up_words=[
        "哎呀,我在呢,有什么事情吗？",
        "啊哈,你叫我了哈,我在听的",
        "来啦,来啦,我醒了,有事情吗？",
        "我当然在呀,怎么啦? 你有什么新点子？",
    ]
    response = random.choice(wake_up_words)
    return response

def is_called_by_user(text):
    client=get_LLM_client()
    prompt = f"""你是一个名叫“知世”的AI语音助手。
            用户刚刚说了下面这句话，即使用户的语音识别结果出现了偏差，比如把“知世”识别成了“知识”、“只是”、“智识”、“芝士”、“姿势”等近音词，你也要尝试判断用户是否是想唤醒你。
            你只需判断：“用户是不是在叫你？”
                下面是用户说的话：
                    “{text}”
            如果是，请回答“是”；如果不是，请回答“否”。不要输出其他内容。
            """

    messages=[{"role":"user","content":prompt}]
    try:
        response=client.chat(messages)
        if hasattr(response,'choices'):
            answer = response.choices[0].message.content.strip()
        elif isinstance(response,dict) and "choices" in response:
            answer = response['choices'][0]["message"]["content"].strip()
        elif isinstance(response,dict) and "error" in response:
            print(f"[判断]AI服务商那里有问题:{type(response)}")
            return False
        else:
            print(f"[判断]唤起AI的智能回答响应格式不对:{type(response)}")
            return False
        
        print(f"[判断]模型返回：{answer}")
        return answer.strip() == "是"
    
    except Exception as e:
        print(f"[判断] 调用AI接口出错:{e}")
        return False

def get_user_intent(text):
    client=get_LLM_client()
    prompt=f"""
    你是一个语义理解助手。用户说了一句话：{text}
    请你判断用户的意图？请从以下五项中选择一个并返回：
    1.播放音乐
    2.暂停音乐
    3.继续播放音乐
    4.停止播放音乐
    5.无操作
    只返回其中一个，且返回只包含汉字,比如选择"1.播放音乐"则返回"播放音乐".
"""
    messages=[{"role":"user","content":prompt}]
    try:
        response=client.chat(messages)
        if hasattr(response,'choices'):
            intent = response.choices[0].message.content.strip()
        elif isinstance(response,dict) and "choices" in response:
            intent = response['choices'][0]["message"]["content"].strip()
        elif isinstance(response,dict) and "error" in response:
            print(f"[意图判断]意图字段不切合AI服务商接口要求:{type(response)}")
            return False
        else:
            print(f"[意图判断]意图判断错误:{type(response)}")
            return False
        
        print(f"[调试]用户输入：{text} 解析出的意图是：{intent}")
    
    except Exception as e:
        print(f"[调试] 不能判断用户的意图?{e}")
        return False
    return intent

def get_answer(messages):
    client = get_LLM_client()
    try:
        response = client.chat(messages)
        if hasattr(response, 'choices'):
            answer = response.choices[0].message.content.strip()
        elif isinstance(response, dict) and "choices" in response:
            answer = response['choices'][0]["message"]["content"].strip()
        elif isinstance(response, dict) and "error" in response:
            print(f"[对话]AI服务商出错:{response}")
            return "抱歉，我这边出了点问题，请再说一次。"
        else:
            print(f"[对话]响应格式不对:{type(response)}")
            return "抱歉，我这边出了点问题，请再说一次。"
        return answer
    except Exception as e:
        print(f"[对话]调用AI接口出错:{e}")
        return "抱歉，我这边出了点问题，请再说一次。"

def optimize_speech_text(text):
    client=get_LLM_client()
    prompt = f"""
        你是一个“语音文本优化器”，负责把助手的回答改写成适合语音朗读的自然口语文本。

        【目标】
        在不改变原意的情况下，让文本更自然、更像真人说话。

        【重要规则】
        1. 不要改变原句意思
        2. 用标点符号控制停顿和节奏：
        - 短停顿用逗号“，”或顿号“、”
        - 句子之间用句号“。”或分号“；”
        - 需要思考或留白时可以用省略号“……”
        3. 不要插入任何特殊符号、标记或英文 token（例如 [uv_break]、[lbreak]、[laugh]），只输出纯中文口语文本
        4. 不要输出解释，不要用引号包裹

        【风格要求】
        - 口语化一点（像真人说话）
        - 有节奏，但不要夸张
        - 适合语音播放

        【用户文本】
        {text}

        【输出】
        """
    response = client.chat([{"role": "user", "content": prompt}])
    if hasattr(response,'choices'):
        optimized_text = response.choices[0].message.content.strip()
    elif isinstance(response,dict) and "choices" in response:
        optimized_text = response['choices'][0]["message"]["content"].strip()
    elif isinstance(response,dict) and "error" in response:
        print(f"[文本优化]文本优化接口出错:{type(response)}")
        return text
    else:
        print(f"[文本优化]文本优化接口响应格式不对:{type(response)}")
        return text
    return optimized_text

def goodbye_responses(goodbye_text):
    client=get_LLM_client()
    prompt = f"""你是一个名叫“知世”的AI语音助手。
            用户刚刚说了下面这句话，你要尝试判断用户是否是想退出对话。
            你只需判断：“用户是不是不想将对话进行下去了？”
            下面是用户说的话：
                    “{goodbye_text}”
            如果是，请回答“是”；如果不是，请回答“否”。不要输出其他内容。
            """

    messages=[{"role":"user","content":prompt}]
    try:
        response=client.chat(messages)
        if hasattr(response,'choices'):
            answer = response.choices[0].message.content.strip()
            if answer == "是":
                return True
            elif answer == "否":
                return False
            return False
        else:
            print(f"[判断]AI判断退出的意愿出错:{type(response)}")
            return False
    except Exception as e:
        print(f"[判断] 判断格式判断退出意愿时出错:{e}")
        return False
