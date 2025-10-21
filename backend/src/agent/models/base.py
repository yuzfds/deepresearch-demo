from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel


class ModelProviderConfig(BaseModel):
    """Configuration for a model provider."""
    name: str
    api_key_env: str
    base_url: Optional[str] = None
    default_models: Dict[str, str] = {}
    description: Optional[str] = None
    supports_structured_output: bool = True
    supports_tools: bool = True
    max_retries: int = 2


class ModelCapabilities(BaseModel):
    """Capabilities of a model."""
    supports_structured_output: bool
    supports_tools: bool
    max_tokens: Optional[int] = None
    temperature_range: tuple[float, float] = (0.0, 2.0)


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, config: ModelProviderConfig):
        self.config = config
        self._api_key: Optional[str] = None

    @property
    def api_key(self) -> str:
        """Get the API key for this provider."""
        if self._api_key is None:
            import os
            self._api_key = os.getenv(self.config.api_key_env)
            if not self._api_key:
                raise ValueError(f"API key not found for provider {self.config.name}. "
                               f"Please set {self.config.api_key_env} environment variable.")
        return self._api_key

    @abstractmethod
    def get_model(
        self,
        model_name: str,
        temperature: float = 0.0,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """Get a language model instance.

        Args:
            model_name: Name of the model to use
            temperature: Temperature for the model
            max_retries: Maximum number of retries
            **kwargs: Additional model-specific parameters

        Returns:
            Configured language model instance
        """
        pass

    @abstractmethod
    def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model capabilities
        """
        pass

    @abstractmethod
    def list_available_models(self) -> List[str]:
        """List available models for this provider.

        Returns:
            List of available model names
        """
        pass

    @abstractmethod
    def validate_model_name(self, model_name: str) -> bool:
        """Validate if a model name is supported.

        Args:
            model_name: Name of the model to validate

        Returns:
            True if model is supported, False otherwise
        """
        pass

    def get_default_model(self, purpose: str) -> str:
        """Get default model for a specific purpose.

        Args:
            purpose: Purpose of the model (e.g., 'query_generator', 'reflection', 'answer')

        Returns:
            Default model name for the purpose
        """
        return self.config.default_models.get(purpose, "")

    def supports_structured_output(self, model_name: str) -> bool:
        """Check if a model supports structured output.

        Args:
            model_name: Name of the model

        Returns:
            True if structured output is supported, False otherwise
        """
        capabilities = self.get_model_capabilities(model_name)
        return capabilities.supports_structured_output

    def create_model_with_structured_output(
        self,
        model_name: str,
        schema_class: Type,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> BaseLanguageModel:
        """Create a model instance with structured output.

        Args:
            model_name: Name of the model
            schema_class: Pydantic model class for structured output
            temperature: Temperature for generation
            **kwargs: Additional model parameters

        Returns:
            Language model instance with structured output
        """
        model = self.get_model(model_name, temperature=temperature, **kwargs)
        return model.with_structured_output(schema_class)

    def supports_feature(self, feature: str, model_name: str) -> bool:
        """Check if a model supports a specific feature.

        Args:
            feature: Feature to check ('structured_output', 'tools')
            model_name: Name of the model

        Returns:
            True if feature is supported, False otherwise
        """
        capabilities = self.get_model_capabilities(model_name)
        if feature == 'structured_output':
            return capabilities.supports_structured_output
        elif feature == 'tools':
            return capabilities.supports_tools
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.config.name}')"