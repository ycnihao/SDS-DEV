#这里是应用中AI接口的配置所在
import json
from pathlib import Path
import os

current_dir = Path(__file__).parent
api_path = current_dir.parent / 'config'/'LLM_api_config.json'

class LLMClient:
    def __init__(self,config_path=api_path):
        self.config = self._load_config(config_path)
        self.active_provider = self.config["model_configs"]["default_provider"]
        self.activate_model = self.config["model_configs"]["default_model"]
        self.clients = self._initialize_clients()

    def _load_config(self,config_path=api_path):
        try:
            with open(config_path,"r",encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"加载API配置时出错?{e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        return {
            "providers": {},
            "model_configs": {
                "default_provider": "deepseek",
                "default_model": "deepseek-chat"
            }
        }
    
    def _initialize_clients(self):
        clients={}
        for provider_name,provider_config in self.config.get("providers",{}).items():
            if provider_name == "deepseek":
                clients[provider_name] = self._create_deepseek_client(provider_config)
            elif provider_name == "openrouter":
                clients[provider_name] = self._create_openrouter_client(provider_config)
        return clients

    def _create_deepseek_client(self,provider_config):
        try:
            from openai import OpenAI
            api_key = provider_config.get("api_key","")
            base_url = provider_config.get("base_url","")
            client = OpenAI(api_key=api_key, base_url=base_url)
            return client
        except Exception as e:
            print(f"创建 deepseek 客户端时出错: {e}")
            return None

    def _create_openrouter_client(self, provider_config):
        try:
            import requests
            api_key = provider_config.get("api_key", "")
            base_url = provider_config.get("base_url", "")
            
            class OpenRouterClient:
                def __init__(self, api_key, base_url):
                    self.api_key = api_key
                    self.base_url = base_url

                def request(self, model, data):
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    response = requests.post(f"{self.base_url}/models/{model}/predict", headers=headers, json=data)
                    return response.json()

            return OpenRouterClient(api_key, base_url)
        except Exception as e:
            print(f"创建 openrouter 客户端时出错: {e}")
            return None
    
    def get_client(self, provider_name=None):
        if provider_name is None:
            provider_name = self.active_provider
        return self.clients.get(provider_name)
    
    def chat(self, messages, model=None, **kwargs):
        client = self.get_client()
        if client is None:
            return {"error": "客户端未初始化?"}
        
        model = model or self.activate_model
        
        if self.active_provider == "deepseek":
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        elif self.active_provider == "openrouter":
            return client.request(model, {"messages": messages, **kwargs})
