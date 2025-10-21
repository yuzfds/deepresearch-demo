import os
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
import re

from langchain_core.runnables import RunnableConfig


class ModelReference(BaseModel):
    """Reference to a specific model with provider information."""
    provider: str = Field(description="Model provider name")
    model: str = Field(description="Model name")

    @classmethod
    def from_string(cls, model_string: str) -> "ModelReference":
        """Parse a model string in format 'provider/model' or just 'model'.

        Examples:
            'aicloud/gpt-oss-120b' -> ModelReference(provider='aicloud', model='gpt-oss-120b')
            'gpt-oss-120b' -> ModelReference(provider='aicloud', model='gpt-oss-120b')  # legacy support
        """
        if '/' in model_string:
            provider, model = model_string.split('/', 1)
            return cls(provider=provider, model=model)
        else:
            # Legacy support - use first available provider for backward compatibility
            from agent.models import get_model_factory
            model_factory = get_model_factory()
            providers = model_factory.list_providers()
            if providers:
                return cls(provider=providers[0], model=model_string)
            else:
                raise ValueError("No model providers configured")

    def __str__(self) -> str:
        return f"{self.provider}/{self.model}"


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="aicloud/gpt-oss-120b",
        metadata={
            "description": "The language model to use for query generation. Format: 'provider/model_name'"
        },
    )

    reflection_model: str = Field(
        default="aicloud/gpt-oss-120b",
        metadata={
            "description": "The language model to use for reflection. Format: 'provider/model_name'"
        },
    )

    answer_model: str = Field(
        default="aicloud/gpt-oss-120b",
        metadata={
            "description": "The language model to use for final answers. Format: 'provider/model_name'"
        },
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "The number of initial search queries to generate."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "The maximum number of research loops to perform."},
    )

    # Model provider specific settings
    model_providers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configuration for individual model providers"
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)

    def get_model_reference(self, field_name: str) -> ModelReference:
        """Get a model reference for a specific configuration field.

        Args:
            field_name: Name of the configuration field (e.g., 'query_generator_model')

        Returns:
            ModelReference instance
        """
        model_string = getattr(self, field_name)
        return ModelReference.from_string(model_string)

    def get_query_generator_ref(self) -> ModelReference:
        """Get the query generator model reference."""
        return self.get_model_reference('query_generator_model')

    def get_reflection_ref(self) -> ModelReference:
        """Get the reflection model reference."""
        return self.get_model_reference('reflection_model')

    def get_answer_ref(self) -> ModelReference:
        """Get the answer model reference."""
        return self.get_model_reference('answer_model')

    def set_model(self, field_name: str, provider: str, model: str):
        """Set a model for a specific configuration field.

        Args:
            field_name: Name of the configuration field
            provider: Model provider name
            model: Model name
        """
        setattr(self, field_name, f"{provider}/{model}")

    def set_query_generator_model(self, provider: str, model: str):
        """Set the query generator model."""
        self.set_model('query_generator_model', provider, model)

    def set_reflection_model(self, provider: str, model: str):
        """Set the reflection model."""
        self.set_model('reflection_model', provider, model)

    def set_answer_model(self, provider: str, model: str):
        """Set the answer model."""
        self.set_model('answer_model', provider, model)

    @classmethod
    def create_with_legacy_defaults(cls) -> "Configuration":
        """Create configuration with legacy defaults for backward compatibility."""
        raise ValueError(
            "Legacy default configuration is no longer supported. "
            "All model providers have been removed."
        )

    def migrate_legacy_models(self):
        """Migrate legacy model names to new format."""
        legacy_fields = ['query_generator_model', 'reflection_model', 'answer_model']

        for field_name in legacy_fields:
            current_value = getattr(self, field_name)
            if not isinstance(current_value, str):
                continue

            # Legacy model format is no longer supported - all providers have been removed
            if '/' not in current_value:
                raise ValueError(
                    f"Legacy model format '{current_value}' is no longer supported. "
                    f"All model providers have been removed."
                )

    def validate_models(self):
        """Validate that all configured models are properly formatted."""
        for field_name in ['query_generator_model', 'reflection_model', 'answer_model']:
            model_string = getattr(self, field_name)
            if '/' not in model_string:
                raise ValueError(
                    f"Model configuration '{field_name}' must be in format 'provider/model_name', "
                    f"got: {model_string}"
                )
