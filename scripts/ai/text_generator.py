"""
Description: Provides functionality for generating text content using AI models.
Handles API communication and text generation requests.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from openai.types.chat import ChatCompletionMessageParam
from ..config.services.user_config import user_config_manager
from llama_cpp import Llama
from openai import OpenAI
from pathlib import Path

user_config = user_config_manager.get_config()


class ITextGenerator(ABC):
    @abstractmethod
    def generate(
        self, history: List[ChatCompletionMessageParam], model: Optional[str] = None
    ) -> str:
        pass


class TextGenerator(ITextGenerator):
    def __init__(
        self, model_name: Optional[str] = None, model_type: Optional[str] = None
    ) -> None:
        self.model_name = model_name or user_config.model.model_type
        self.model_type = model_type or user_config.model.model_type
        self.model = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the model based on model_type and model_name."""
        if self.model_type == "online":
            self.model = OpenAI(
                base_url=user_config.openrouter.base_url,
                api_key=user_config.openrouter.api_key.get_secret_value(),
            )
        else:
            model_dir = Path(__file__).parent.parent.parent / "local_models"
            model_path = next(model_dir.rglob(self.model_name))

            self.model = Llama(
                model_path=str(model_path),
                n_gpu_layers=user_config.local.n_gpu_layers,
                use_mlock=user_config.local.use_mlock,
                flash_attn=user_config.local.flash_attn,
                n_ctx=user_config.local.n_ctx,
                chat_format=user_config.local.chat_format,
            )

    def generate(
        self, history: List[ChatCompletionMessageParam], model: Optional[str] = None
    ) -> str:
        model_name = model or self.model_name
        try:
            if self.model_type == "online":
                # OpenAI-style API
                completion = self.model.chat.completions.create(
                    model=model_name,
                    messages=history,
                    max_tokens=2048,
                    temperature=0.7,
                )
                content = completion.choices[0].message.content
            else:
                print("-"*100)
                print(history)
                print("-"*100)
                messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in history
                    if isinstance(msg, dict)
                ]

                output = self.model.create_chat_completion(
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.7,
                )
                content = output["choices"][0]["message"]["content"]

            if not content:
                raise ValueError("Empty response from model")
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {str(e)}")

    def change_model(self, model_name: str, model_type: str) -> None:
        """Change the model and reinitialize the client."""
        self.model_name = model_name
        self.model_type = model_type
        self._initialize_model()
