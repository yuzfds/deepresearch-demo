import os
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
import re

from langchain_core.runnables import RunnableConfig


class ModelReference(BaseModel):
    """Reference to a specific model with provider information."""
    provider: str = Field(default="aicloud_glm45", description="Model provider name")
    model: str = Field(description="Model name")

    @classmethod
    def from_string(cls, model_string: str) -> "ModelReference":
        """Parse a model string in format 'provider/model' or just 'model'.

        Examples:
            'openai_compatible/gpt-4' -> ModelReference(provider='openai_compatible', model='gpt-4')
            'gpt-4' -> ModelReference(provider='openai_compatible', model='gpt-4')  # legacy support
        """
        if '/' in model_string:
            provider, model = model_string.split('/', 1)
            return cls(provider=provider, model=model)
        else:
            # Legacy support - assume aicloud_glm45 provider for backward compatibility
            return cls(provider="aicloud_glm45", model=model_string)

    def __str__(self) -> str:
        return f"{self.provider}/{self.model}"


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="aicloud_glm45/glm-4.5",
        metadata={
            "description": "The language model to use for query generation. Format: 'provider/model_name'"
        },
    )

    reflection_model: str = Field(
        default="aicloud_glm45/glm-4.5",
        metadata={
            "description": "The language model to use for reflection. Format: 'provider/model_name'"
        },
    )

    answer_model: str = Field(
        default="aicloud_glm45/glm-4.5",
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
        return cls(
            query_generator_model="gpt-4",
            reflection_model="gpt-4",
            answer_model="gpt-4"
        )

    def migrate_legacy_models(self):
        """Migrate legacy model names to new format."""
        legacy_fields = ['query_generator_model', 'reflection_model', 'answer_model']

        for field_name in legacy_fields:
            current_value = getattr(self, field_name)
            if not isinstance(current_value, str):
                continue

            # If it doesn't contain a provider, assume it's a legacy openai_compatible model
            if '/' not in current_value and not current_value.startswith('openai_compatible/'):
                setattr(self, field_name, f"openai_compatible/{current_value}")

    def validate_models(self):
        """Validate that all configured models are properly formatted."""
        for field_name in ['query_generator_model', 'reflection_model', 'answer_model']:
            model_string = getattr(self, field_name)
            if '/' not in model_string:
                raise ValueError(
                    f"Model configuration '{field_name}' must be in format 'provider/model_name', "
                    f"got: {model_string}"
                )
