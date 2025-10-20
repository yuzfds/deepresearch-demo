from typing import List, Optional, Any, Dict
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from .base import ModelProvider, ModelProviderConfig, ModelCapabilities


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible models."""

    def __init__(self, config: ModelProviderConfig):
        super().__init__(config)
        self._supported_models: Optional[List[str]] = None

    def get_model(
        self,
        model_name: str,
        temperature: float = 0.0,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """Get an OpenAI-compatible language model instance.

        Args:
            model_name: Name of the model to use
            temperature: Temperature for the model
            max_retries: Maximum number of retries
            **kwargs: Additional model-specific parameters

        Returns:
            Configured ChatOpenAI instance
        """
        if not self.validate_model_name(model_name):
            raise ValueError(f"Model '{model_name}' is not supported by provider '{self.config.name}'")

        retries = max_retries or self.config.max_retries

        model_kwargs = {
            "model": model_name,
            "temperature": temperature,
            "max_retries": retries,
            "api_key": self.api_key,
            **kwargs
        }

        # Add base_url if configured
        if self.config.base_url:
            model_kwargs["base_url"] = self.config.base_url

        return ChatOpenAI(**model_kwargs)

    def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific OpenAI-compatible model.

        Args:
            model_name: Name of the model

        Returns:
            Model capabilities
        """
        # Common capabilities for most OpenAI-compatible models
        capabilities = ModelCapabilities(
            supports_structured_output=self.config.supports_structured_output,
            supports_tools=self.config.supports_tools,
            max_tokens=128000,  # Default for most modern models
            temperature_range=(0.0, 2.0)
        )

        # Adjust based on known model patterns
        model_lower = model_name.lower()

        # GPT-3.5 models
        if 'gpt-3.5' in model_lower:
            capabilities.max_tokens = 16385
            capabilities.supports_structured_output = False  # Limited support

        # GPT-4 models
        elif 'gpt-4' in model_lower:
            capabilities.max_tokens = 128000
            capabilities.supports_structured_output = True

        # Claude models (if using Anthropic API)
        elif 'claude' in model_lower:
            capabilities.max_tokens = 200000
            capabilities.supports_structured_output = True

        # Local models typically have conservative defaults
        elif any(local_indicator in model_lower for local_indicator in ['llama', 'mistral', 'mixtral']):
            capabilities.max_tokens = 8192
            capabilities.supports_structured_output = False
            capabilities.supports_tools = False

        return capabilities

    def list_available_models(self) -> List[str]:
        """List available models for this OpenAI-compatible provider.

        Returns:
            List of available model names
        """
        if self._supported_models is not None:
            return self._supported_models

        # Common OpenAI model names
        openai_models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

        # Common local model names
        local_models = [
            "llama-3.1-8b",
            "llama-3.1-70b",
            "llama-3-8b",
            "llama-3-70b",
            "mistral-7b",
            "mixtral-8x7b",
            "qwen-7b",
            "qwen-14b",
            "qwen-32b"
        ]

        # If this is the default OpenAI provider, return OpenAI models
        if self.config.base_url == "https://api.openai.com/v1":
            self._supported_models = openai_models
        else:
            # For custom endpoints, combine both lists
            self._supported_models = openai_models + local_models

        return self._supported_models

    def validate_model_name(self, model_name: str) -> bool:
        """Validate if a model name is supported.

        Args:
            model_name: Name of the model to validate

        Returns:
            True if model is supported, False otherwise
        """
        # For now, accept any model name for OpenAI-compatible providers
        # In practice, you might want to validate against the actual API
        return bool(model_name and isinstance(model_name, str))

    def supports_structured_output(self, model_name: str) -> bool:
        """Check if a model supports structured output.

        Args:
            model_name: Name of the model

        Returns:
            True if structured output is supported
        """
        capabilities = self.get_model_capabilities(model_name)
        return capabilities.supports_structured_output

    def supports_tools(self, model_name: str) -> bool:
        """Check if a model supports tools/function calling.

        Args:
            model_name: Name of the model

        Returns:
            True if tools are supported
        """
        capabilities = self.get_model_capabilities(model_name)
        return capabilities.supports_tools

    def get_max_tokens(self, model_name: str) -> Optional[int]:
        """Get the maximum tokens for a model.

        Args:
            model_name: Name of the model

        Returns:
            Maximum tokens or None if unknown
        """
        capabilities = self.get_model_capabilities(model_name)
        return capabilities.max_tokens

    def get_temperature_range(self, model_name: str) -> tuple[float, float]:
        """Get the valid temperature range for a model.

        Args:
            model_name: Name of the model

        Returns:
            Tuple of (min_temp, max_temp)
        """
        capabilities = self.get_model_capabilities(model_name)
        return capabilities.temperature_range

    def create_model_with_structured_output(
        self,
        model_name: str,
        output_schema: Any,
        temperature: float = 0.0,
        **kwargs
    ) -> BaseLanguageModel:
        """Create a model with structured output capabilities.

        Args:
            model_name: Name of the model
            output_schema: The output schema for structured generation
            temperature: Temperature for the model
            **kwargs: Additional model parameters

        Returns:
            Model configured for structured output
        """
        if not self.supports_structured_output(model_name):
            raise ValueError(f"Model '{model_name}' does not support structured output")

        base_model = self.get_model(model_name, temperature=temperature, **kwargs)
        return base_model.with_structured_output(output_schema)

    def create_model_with_tools(
        self,
        model_name: str,
        tools: List[Any],
        temperature: float = 0.0,
        **kwargs
    ) -> BaseLanguageModel:
        """Create a model with tool capabilities.

        Args:
            model_name: Name of the model
            tools: List of tools to bind to the model
            temperature: Temperature for the model
            **kwargs: Additional model parameters

        Returns:
            Model configured with tools
        """
        if not self.supports_tools(model_name):
            raise ValueError(f"Model '{model_name}' does not support tools")

        base_model = self.get_model(model_name, temperature=temperature, **kwargs)
        return base_model.bind_tools(tools)

    def __str__(self) -> str:
        return f"OpenAICompatibleProvider(name='{self.config.name}', base_url='{self.config.base_url}')"