"""Ollama client wrapper for TinyLlama interaction"""

import ollama
from typing import Optional, Dict, Any, List
import logging
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class OllamaClient:
    """Wrapper for Ollama API interaction with TinyLlama"""

    def __init__(self, model: str = "tinyllama:latest", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.client = ollama.Client()
        self._verify_model()

    def _verify_model(self):
        """Verify that the model is available"""
        try:
            response = self.client.list()
            model_names = []

            # Handle the ollama ListResponse object
            if hasattr(response, 'models'):
                for model in response.models:
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    elif isinstance(model, dict) and 'model' in model:
                        model_names.append(model['model'])
            elif isinstance(response, dict) and 'models' in response:
                for model in response['models']:
                    if isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])

            if self.model not in model_names:
                console.print(f"[yellow]Warning: Model {self.model} not found. Available models: {model_names}[/yellow]")
                if 'tinyllama:latest' in model_names:
                    self.model = 'tinyllama:latest'
                    console.print(f"[green]Using tinyllama:latest instead[/green]")
                else:
                    raise ValueError(f"TinyLlama model not found. Please run: ollama pull tinyllama")
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"Could not verify model list: {e}")
            # Try to continue anyway
            console.print(f"[yellow]Could not verify models, attempting to use {self.model} anyway[/yellow]")

    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate a response from the model"""
        try:
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', 2048),
            }

            messages = []
            if system:
                messages.append({'role': 'system', 'content': system})
            messages.append({'role': 'user', 'content': prompt})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options
            )

            return response['message']['content']
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def stream_generate(self, prompt: str, system: Optional[str] = None, **kwargs):
        """Stream responses from the model"""
        try:
            options = {
                'temperature': kwargs.get('temperature', self.temperature),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', 2048),
            }

            messages = []
            if system:
                messages.append({'role': 'system', 'content': system})
            messages.append({'role': 'user', 'content': prompt})

            stream = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
                stream=True
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for context"""
        # Placeholder for conversation history management
        return []