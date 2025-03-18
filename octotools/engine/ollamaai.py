import os
import json
import base64
import platformdirs
import ollama
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import List, Union
from dotenv import load_dotenv

from .base import EngineLM, CachedEngine
from pydantic import BaseModel

load_dotenv()

class DefaultFormat(BaseModel):
    response: str

# FIXME Define global constant for structured models
OLLAMA_STRUCTURED_MODELS = ["mistral", "gemma", "llama3"]

class ChatOllama(EngineLM, CachedEngine):
    DEFAULT_SYSTEM_PROMPT = "You are a helpful, creative, and smart assistant."

    def __init__(
        self,
        model_string="mistral",
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        is_multimodal: bool = False,
        enable_cache: bool = True,
        **kwargs
    ):
        """
        :param model_string: The Ollama model to use.
        :param system_prompt: Default system instructions.
        :param is_multimodal: If True, supports multimodal input.
        """
        if enable_cache:
            root = platformdirs.user_cache_dir("octotools")
            cache_path = os.path.join(root, f"cache_ollama_{model_string}.db")

            self.image_cache_dir = os.path.join(root, "image_cache")
            os.makedirs(self.image_cache_dir, exist_ok=True)

            super().__init__(cache_path=cache_path)

        self.system_prompt = system_prompt
        self.model_string = model_string
        self.is_multimodal = is_multimodal
        self.enable_cache = enable_cache

        if enable_cache:
            print(f"!! Cache enabled for model: {self.model_string}")
        else:
            print(f"!! Cache disabled for model: {self.model_string}")

    @retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(5))
    def generate(self, content: Union[str, List[Union[str, bytes]]], system_prompt=None, **kwargs):
        try:
            attempt_number = self.generate.retry.statistics.get("attempt_number", 0) + 1
            if attempt_number > 1:
                print(f"Attempt {attempt_number} of 5")

            if isinstance(content, str):
                return self._generate_text(content, system_prompt=system_prompt, **kwargs)

            elif isinstance(content, list):
                if not self.is_multimodal:
                    raise NotImplementedError("Multimodal generation is not supported for all Ollama models.")
                return self._generate_multimodal(content, system_prompt=system_prompt, **kwargs)

        except ollama.OllamaError as e:
            print(f"Ollama API error: {str(e)}")
            return {"error": "ollama_api_error", "message": str(e), "details": getattr(e, "args", None)}
        except Exception as e:
            print(f"Error in generate method: {str(e)}")
            return {"error": type(e).__name__, "message": str(e), "details": getattr(e, "args", None)}

    def _generate_text(self, prompt, system_prompt=None, temperature=0, max_tokens=4000, top_p=0.99, response_format=None):
        sys_prompt_arg = system_prompt if system_prompt else self.system_prompt

        if self.enable_cache:
            cache_key = sys_prompt_arg + prompt
            cache_or_none = self._check_cache(cache_key)
            if cache_or_none is not None:
                return cache_or_none

        messages = [
            {"role": "system", "content": sys_prompt_arg},
            {"role": "user", "content": prompt},
        ]

        response = ollama.chat(
            model=self.model_string,
            messages=messages,
            temperature=temperature,
            num_predict=max_tokens,
            top_p=top_p,
        )

        response_text = response.get("message", {}).get("content", "")

        if self.enable_cache:
            self._save_cache(cache_key, response_text)
        return response_text

    def __call__(self, prompt, **kwargs):
        return self.generate(prompt, **kwargs)

    def _format_content(self, content: List[Union[str, bytes]]) -> List[dict]:
        formatted_content = []
        for item in content:
            if isinstance(item, bytes):
                base64_image = base64.b64encode(item).decode("utf-8")
                formatted_content.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                )
            elif isinstance(item, str):
                formatted_content.append({"type": "text", "text": item})
            else:
                raise ValueError(f"Unsupported input type: {type(item)}")
        return formatted_content

    def _generate_multimodal(self, content: List[Union[str, bytes]], system_prompt=None, temperature=0, max_tokens=4000, top_p=0.99, response_format=None):
        sys_prompt_arg = system_prompt if system_prompt else self.system_prompt
        formatted_content = self._format_content(content)

        if self.enable_cache:
            cache_key = sys_prompt_arg + json.dumps(formatted_content)
            cache_or_none = self._check_cache(cache_key)
            if cache_or_none is not None:
                return cache_or_none

        messages = [
            {"role": "system", "content": sys_prompt_arg},
            {"role": "user", "content": formatted_content},
        ]

        response = ollama.chat(
            model=self.model_string,
            messages=messages,
            temperature=temperature,
            num_predict=max_tokens,
            top_p=top_p,
        )

        response_text = response.get("message", {}).get("content", "")

        if self.enable_cache:
            self._save_cache(cache_key, response_text)
        return response_text