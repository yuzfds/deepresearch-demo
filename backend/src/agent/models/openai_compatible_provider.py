"""OpenAI-compatible provider implementation."""

from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from .base import ModelProvider, ModelProviderConfig, ModelCapabilities


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible APIs."""

    def __init__(self, config: ModelProviderConfig):
        super().__init__(config)
        self._models_cache: Optional[List[str]] = None

    def get_model(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> BaseLanguageModel:
        """Get a language model instance.

        Args:
            model_name: Name of the model
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            Language model instance
        """
        if not self.validate_model_name(model_name):
            raise ValueError(f"Model {model_name} is not supported by provider {self.config.name}")

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=self.api_key,
            openai_api_base=self.config.base_url,
            max_retries=self.config.max_retries,
            **kwargs
        )

    def list_available_models(self) -> List[str]:
        """List available models for this provider.

        Returns:
            List of available model names
        """
        if self._models_cache is None:
            # For OpenAI-compatible providers, we use the default models from config
            # or fall back to common model names
            if self.config.default_models:
                self._models_cache = list(set(self.config.default_models.values()))
            else:
                # Fallback to a common model name
                self._models_cache = ["gpt-3.5-turbo"]

        return self._models_cache

    def validate_model_name(self, model_name: str) -> bool:
        """Validate if a model name is supported.

        Args:
            model_name: Name of the model to validate

        Returns:
            True if model is supported, False otherwise
        """
        available_models = self.list_available_models()
        return model_name in available_models

    def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model capabilities
        """
        return ModelCapabilities(
            supports_structured_output=self.config.supports_structured_output,
            supports_tools=self.config.supports_tools,
            max_tokens=None,  # Will be determined by the specific model
            temperature_range=(0.0, 2.0)
        )

    def get_default_model(self, task_type: str = "query_generator") -> Optional[str]:
        """Get the default model for a specific task type.

        Args:
            task_type: Type of task (query_generator, reflection, answer)

        Returns:
            Default model name or None if not configured
        """
        return self.config.default_models.get(task_type)