#!/usr/bin/env python3
"""
Test script to verify that AICloud GLM-4.5 is set as the default model.
"""

import sys
import os
sys.path.append('src')

def test_default_configuration():
    """Test that AICloud GLM-4.5 is the default configuration."""
    try:
        from agent.models import get_model_factory, reset_model_factory
        from agent.configuration import Configuration
        print("+ Default configuration test started")

        # Reset factory to ensure clean state
        reset_model_factory()

        # Get the factory instance
        factory = get_model_factory()
        print("+ Model factory instance created")

        # List providers (should have aicloud_glm45 first)
        providers = factory.list_providers()
        print(f"+ Available providers: {providers}")

        # Check that aicloud_glm45 is the first provider
        if providers and providers[0] == 'aicloud_glm45':
            print("+ AICloud GLM-4.5 is the first provider (correct)")
        else:
            print(f"[ERROR] Expected aicloud_glm45 as first provider, got: {providers[0] if providers else 'None'}")
            return False

        # Test default configuration
        config = Configuration()
        print(f"+ Default query generator model: {config.query_generator_model}")
        print(f"+ Default reflection model: {config.reflection_model}")
        print(f"+ Default answer model: {config.answer_model}")

        # Check that all default models are aicloud_glm45/glm-4.5
        expected_model = "aicloud_glm45/glm-4.5"
        if (config.query_generator_model == expected_model and
            config.reflection_model == expected_model and
            config.answer_model == expected_model):
            print("+ All default models are set to AICloud GLM-4.5 (correct)")
        else:
            print(f"[ERROR] Expected all models to be {expected_model}")
            print(f"  Got query_generator: {config.query_generator_model}")
            print(f"  Got reflection: {config.reflection_model}")
            print(f"  Got answer: {config.answer_model}")
            return False

        # Test ModelReference default provider
        from agent.configuration import ModelReference
        model_ref = ModelReference(model="glm-4.5")
        print(f"+ ModelReference default provider: {model_ref.provider}")

        if model_ref.provider == 'aicloud_glm45':
            print("+ ModelReference default provider is AICloud (correct)")
        else:
            print(f"[ERROR] Expected ModelReference default provider to be aicloud_glm45, got: {model_ref.provider}")
            return False

        # Test ModelReference from_string legacy support
        legacy_ref = ModelReference.from_string("glm-4.5")
        print(f"+ ModelReference legacy support: {legacy_ref}")

        if legacy_ref.provider == 'aicloud_glm45' and legacy_ref.model == 'glm-4.5':
            print("+ ModelReference legacy support works correctly (correct)")
        else:
            print(f"[ERROR] Expected aicloud_glm45/glm-4.5, got: {legacy_ref}")
            return False

        print("\n[OK] All default configuration tests passed!")
        return True

    except Exception as e:
        print(f"[ERROR] Default configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_default_configuration()