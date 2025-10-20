import os
from typing import Dict, List, Optional, Type
import yaml
from .base import ModelProvider, ModelProviderConfig
from .openai_compatible_provider import OpenAICompatibleProvider


class ModelFactory:
    """Factory for creating model providers."""

    def __init__(self, config_path: Optional[str] = None):
        self._providers: Dict[str, ModelProvider] = {}
        self._provider_configs: Dict[str, ModelProviderConfig] = {}
        self._config_path = config_path or self._get_default_config_path()
        self._load_configs()

    def _get_default_config_path(self) -> str:
        """Get the default path for model configuration."""
        # Check for config file in multiple locations
        possible_paths = [
            "config/models.yaml",
            "models.yaml",
            os.path.join(os.path.dirname(__file__), "../../../config/models.yaml"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # If no config file found, return default path
        return "config/models.yaml"

    def _load_configs(self):
        """Load model provider configurations from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                if 'providers' in config_data:
                    for provider_name, provider_data in config_data['providers'].items():
                        config = ModelProviderConfig(
                            name=provider_name,
                            **provider_data
                        )
                        self._provider_configs[provider_name] = config
            except Exception as e:
                print(f"Warning: Failed to load model config from {self._config_path}: {e}")

        # Always add default OpenAI compatible config if not present
        if 'openai_compatible' not in self._provider_configs:
            self._provider_configs['openai_compatible'] = ModelProviderConfig(
                name='openai_compatible',
                api_key_env='OPENAI_API_KEY',
                base_url='https://api.openai.com/v1',
                default_models={
                    'query_generator': 'gpt-4',
                    'reflection': 'gpt-4',
                    'answer': 'gpt-4'
                },
                description='OpenAI compatible models (including custom endpoints)',
                supports_structured_output=True,
                supports_tools=True,
                max_retries=2
            )

        
    def register_provider(self, provider_class: Type[ModelProvider], config: ModelProviderConfig):
        """Register a new model provider class."""
        provider = provider_class(config)
        self._providers[config.name] = provider

    def get_provider(self, provider_name: str) -> ModelProvider:
        """Get a model provider instance.

        Args:
            provider_name: Name of the provider

        Returns:
            Model provider instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider_name not in self._providers:
            if provider_name in self._provider_configs:
                # Create provider instance on demand
                config = self._provider_configs[provider_name]
                # All configured providers are assumed to be OpenAI compatible
                self.register_provider(OpenAICompatibleProvider, config)
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")

        return self._providers[provider_name]

    def list_providers(self) -> List[str]:
        """List all available provider names.

        Returns:
            List of provider names
        """
        return list(self._provider_configs.keys())

    def get_provider_config(self, provider_name: str) -> Optional[ModelProviderConfig]:
        """Get configuration for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider configuration or None if not found
        """
        return self._provider_configs.get(provider_name)

    def list_models_for_provider(self, provider_name: str) -> List[str]:
        """List available models for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            List of available model names
        """
        provider = self.get_provider(provider_name)
        return provider.list_available_models()

    def get_model(self, provider_name: str, model_name: str, **kwargs) -> 'BaseLanguageModel':
        """Get a language model instance from a provider.

        Args:
            provider_name: Name of the provider
            model_name: Name of the model
            **kwargs: Additional model parameters

        Returns:
            Language model instance
        """
        provider = self.get_provider(provider_name)
        return provider.get_model(model_name, **kwargs)

    def validate_model(self, provider_name: str, model_name: str) -> bool:
        """Validate if a model is supported by a provider.

        Args:
            provider_name: Name of the provider
            model_name: Name of the model

        Returns:
            True if model is supported, False otherwise
        """
        try:
            provider = self.get_provider(provider_name)
            return provider.validate_model_name(model_name)
        except ValueError:
            return False

    def reload_configs(self):
        """Reload configurations from file."""
        self._providers.clear()
        self._provider_configs.clear()
        self._load_configs()

    def create_default_config_file(self, path: str = "config/models.yaml"):
        """Create a default configuration file.

        Args:
            path: Path to create the config file
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        default_config = {
            'providers': {
                'openai_compatible': {
                    'name': 'openai_compatible',
                    'api_key_env': 'OPENAI_API_KEY',
                    'base_url': 'https://api.openai.com/v1',
                    'default_models': {
                        'query_generator': 'gpt-4',
                        'reflection': 'gpt-4',
                        'answer': 'gpt-4'
                    },
                    'description': 'OpenAI compatible models (including custom endpoints)',
                    'supports_structured_output': True,
                    'supports_tools': True,
                    'max_retries': 2
                }
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)


# Global model factory instance
_model_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """Get the global model factory instance.

    Returns:
        Model factory instance
    """
    global _model_factory
    if _model_factory is None:
        _model_factory = ModelFactory()
    return _model_factory


def reset_model_factory():
    """Reset the global model factory instance."""
    global _model_factory
    _model_factory = None