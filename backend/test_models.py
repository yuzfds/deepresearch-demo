#!/usr/bin/env python3
"""
Simple test script to verify the model provider system works.
"""

import sys
import os
sys.path.append('src')

def test_model_factory():
    """Test that the model factory can be created and lists providers."""
    try:
        from agent.models import get_model_factory, reset_model_factory
        print("+ Model factory imported successfully")

        # Reset factory to ensure clean state
        reset_model_factory()

        # Get the factory instance
        factory = get_model_factory()
        print("+ Model factory instance created")

        # List providers
        providers = factory.list_providers()
        print(f"+ Available providers: {providers}")

        # Test OpenAI compatible provider (default)
        if 'openai_compatible' in providers:
            openai_provider = factory.get_provider('openai_compatible')
            print("+ OpenAI compatible provider created")

            openai_models = openai_provider.list_available_models()
            print(f"+ OpenAI models: {len(openai_models)} models available")

            # Test getting the default provider
            default_provider = factory.get_provider('openai_compatible')
            print(f"+ Default provider: openai_compatible")

        # Test Anthropic provider (if available)
        if 'anthropic' in providers:
            anthropic_provider = factory.get_provider('anthropic')
            print("+ Anthropic provider created")

            anthropic_models = anthropic_provider.list_available_models()
            print(f"+ Anthropic models: {len(anthropic_models)} models available")

        print("\n[OK] All tests passed!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_model_factory()