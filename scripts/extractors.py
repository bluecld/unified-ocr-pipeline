import yaml
import re
import requests
import os

class RegexExtractor:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.fields = self.config.get('fields', {})

    def extract(self, text):
        result = {}
        for field, props in self.fields.items():
            pattern = props.get('regex')
            if pattern:
                match = re.search(pattern, text, re.MULTILINE)
                result[field] = match.group(1) if match else None
        return result

class AIExtractor:
    def __init__(self, config_path, ollama_host=None):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.prompt = self.config.get('ai_prompt', '')
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'http://ollama:11434')

    def extract(self, text):
        payload = {
            "model": "llama2:7b-chat",
            "prompt": f"{self.prompt}\n\n{text}",
            "stream": False
        }
        try:
            resp = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=60)
            resp.raise_for_status()
            response_json = resp.json()
            # Expecting JSON in response
            return response_json.get('response', {})
        except Exception as e:
            return {"error": str(e)}

def get_extractor(engine_type, config_path, ollama_host=None):
    if engine_type == 'ai':
        return AIExtractor(config_path, ollama_host)
    return RegexExtractor(config_path)
