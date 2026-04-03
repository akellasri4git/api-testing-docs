import os
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from core.logger import setup_logger

logger = setup_logger("LLMClient")

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """
    Unified LLM client supporting multiple providers:
    - Ollama (local)
    - OpenAI
    - Anthropic
    - Groq
    - Azure OpenAI

    Configure via .env file.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        timeout: int = 600
    ):
        # Load from environment or use provided values
        self.provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "600"))

        # Initialize provider-specific settings
        self._setup_provider(model, api_key, base_url)

        logger.info(f"LLM initialized | provider={self.provider} | model={self.model}")

    def _setup_provider(self, model: Optional[str], api_key: Optional[str], base_url: Optional[str]):
        """Setup provider-specific configuration"""

        if self.provider == "ollama":
            self._setup_ollama(model, base_url)
        elif self.provider == "openai":
            self._setup_openai(model, api_key, base_url)
        elif self.provider == "anthropic":
            self._setup_anthropic(model, api_key, base_url)
        elif self.provider == "groq":
            self._setup_groq(model, api_key, base_url)
        elif self.provider == "azure":
            self._setup_azure(model, api_key, base_url)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _setup_ollama(self, model: Optional[str], base_url: Optional[str]):
        """Setup Ollama (local) provider"""
        import requests

        self.model = model or os.getenv("OLLAMA_MODEL", "mistral:latest")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.api_key = None

        self.session = requests.Session()
        self.session.trust_env = False

    def _setup_openai(self, model: Optional[str], api_key: Optional[str], base_url: Optional[str]):
        """Setup OpenAI provider"""
        from openai import OpenAI

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file.")

        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _setup_anthropic(self, model: Optional[str], api_key: Optional[str], base_url: Optional[str]):
        """Setup Anthropic provider"""
        from anthropic import Anthropic

        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY in .env file.")

        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

        if self.base_url:
            self.client = Anthropic(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = Anthropic(api_key=self.api_key)

    def _setup_groq(self, model: Optional[str], api_key: Optional[str], base_url: Optional[str]):
        """Setup Groq provider (uses OpenAI-compatible API)"""
        from openai import OpenAI

        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY in .env file.")

        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _setup_azure(self, model: Optional[str], api_key: Optional[str], base_url: Optional[str]):
        """Setup Azure OpenAI provider"""
        from openai import AzureOpenAI

        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not self.api_key or not azure_endpoint:
            raise ValueError("Azure OpenAI API key and endpoint required. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env file.")

        self.model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Send chat completion request to the configured LLM provider.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Generated text response
        """
        logger.info(f"Sending request to {self.provider}")
        start_time = time.time()

        try:
            if self.provider == "ollama":
                response = self._chat_ollama(messages)
            elif self.provider == "anthropic":
                response = self._chat_anthropic(messages)
            elif self.provider in ["openai", "groq", "azure"]:
                response = self._chat_openai_compatible(messages)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            duration = round(time.time() - start_time, 2)
            logger.info(f"{self.provider.capitalize()} completed in {duration}s")

            return response

        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise

    def _chat_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Ollama-specific chat implementation"""
        import requests
        import json

        # Convert messages to Ollama prompt format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}:\n{content}")

        prompt = "\n\n".join(prompt_parts) + "\n\nASSISTANT:\n"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        response = self.session.post(
            f"{self.base_url}/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            stream=True,
            timeout=self.timeout
        )

        if response.status_code != 200:
            error_msg = f"Ollama error {response.status_code}: {response.text}"

            if response.status_code == 404 and "not found" in response.text:
                logger.error(f"\nModel '{self.model}' not found in Ollama.")
                logger.error("Available models: Run 'ollama list' to see installed models")
                logger.error(f"To install this model: ollama pull {self.model}")

            raise RuntimeError(error_msg)

        output = []
        for line in response.iter_lines():
            if not line:
                continue

            chunk = json.loads(line.decode("utf-8"))

            if "response" in chunk:
                output.append(chunk["response"])

            if chunk.get("done"):
                break

        return "".join(output)

    def _chat_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """Anthropic-specific chat implementation"""

        # Separate system message from other messages
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Call Anthropic API
        kwargs = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        if system_message:
            kwargs["system"] = system_message

        response = self.client.messages.create(**kwargs)

        return response.content[0].text

    def _chat_openai_compatible(self, messages: List[Dict[str, str]]) -> str:
        """OpenAI-compatible chat implementation (OpenAI, Groq, Azure)"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )

        return response.choices[0].message.content
