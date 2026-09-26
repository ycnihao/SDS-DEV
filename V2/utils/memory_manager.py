import json
from pathlib import Path
import os

current_dir = Path(__file__).parent
memory_path = current_dir.parent /'data'/'memory.json'
def load_memory():
    try:
        with open(memory_path,"r",encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"你的记忆文件没找到,你可以看看对应文件夹data里有没有")
        return{}
    except json.JSONDecodeError as e:
        print(f"Json解析错误,你可以看看你的记忆文件是不是json格式或者是帮助你json化记忆文件的工具有错误:{e}")
        return{}
    except Exception as e:
        print(f"加载出错,可以排查一下是不是设备的问题:{e}")
        return{}
    
def update_memory(key,value):
    memory=load_memory()
    if key in memory:
        if isinstance(memory[key],list) and value not in memory[key]:
            memory[key].append(value)
    else:
        memory[key]=[value]
    with open(memory_path,'w',encoding="utf-8")as f:
        json.dump(memory,f,ensure_ascii=False,indent=2)

