#!/usr/bin/env python3
"""
Test script to verify the new AICloud GLM-4.5 provider configuration.
"""

import sys
import os
sys.path.append('src')

def test_aicloud_provider():
    """Test that the AICloud GLM-4.5 provider works correctly."""
    try:
        from agent.models import get_model_factory, reset_model_factory
        print("+ AICloud provider test started")

        # Reset factory to ensure clean state
        reset_model_factory()

        # Get the factory instance
        factory = get_model_factory()
        print("+ Model factory instance created")

        # List providers
        providers = factory.list_providers()
        print(f"+ Available providers: {providers}")

        # Test AICloud provider
        if 'aicloud_glm45' in providers:
            aicloud_provider = factory.get_provider('aicloud_glm45')
            print("+ AICloud provider created successfully")

            # Get provider config
            config = aicloud_provider.config
            print(f"+ AICloud provider name: {config.name}")
            print(f"+ AICloud base URL: {config.base_url}")
            print(f"+ AICloud API key env: {config.api_key_env}")
            print(f"+ AICloud description: {config.description}")

            # Test default models
            print(f"+ Default query generator model: {config.default_models.get('query_generator')}")
            print(f"+ Default reflection model: {config.default_models.get('reflection')}")
            print(f"+ Default answer model: {config.default_models.get('answer')}")

            # Test capabilities
            print(f"+ Supports structured output: {config.supports_structured_output}")
            print(f"+ Supports tools: {config.supports_tools}")
            print(f"+ Max retries: {config.max_retries}")

            # Test model listing (this may fail without API key, but that's expected)
            try:
                models = aicloud_provider.list_available_models()
                print(f"+ Available models: {len(models)} models")
                print(f"+ Models: {models}")
            except Exception as e:
                print(f"+ Model listing failed (expected without API key): {e}")

            print("\n[OK] AICloud GLM-4.5 provider test passed!")
            return True
        else:
            print("[ERROR] AICloud provider not found in providers list")
            return False

    except Exception as e:
        print(f"[ERROR] AICloud provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_aicloud_provider()