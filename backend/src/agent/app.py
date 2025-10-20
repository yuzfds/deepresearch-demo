# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Any
import pydantic

# Define the FastAPI app
app = FastAPI()

# Import model factory
from agent.models import get_model_factory


class ModelInfo(pydantic.BaseModel):
    """Model information for frontend."""
    id: str
    name: str
    provider: str
    description: str = ""


class ProviderInfo(pydantic.BaseModel):
    """Provider information for frontend."""
    name: str
    description: str = ""
    models: List[ModelInfo]


@app.get("/api/models/providers")
async def get_providers() -> List[ProviderInfo]:
    """Get all available model providers and their models."""
    try:
        model_factory = get_model_factory()
        providers = model_factory.list_providers()

        result = []
        for provider_name in providers:
            try:
                provider = model_factory.get_provider(provider_name)
                config = model_factory.get_provider_config(provider_name)
                models = provider.list_available_models()

                model_infos = []
                for model in models:
                    model_info = ModelInfo(
                        id=f"{provider_name}/{model}",
                        name=model,
                        provider=provider_name,
                        description=f"{provider_name} model: {model}"
                    )
                    model_infos.append(model_info)

                provider_info = ProviderInfo(
                    name=provider_name,
                    description=config.description or f"{provider_name} provider",
                    models=model_infos
                )
                result.append(provider_info)
            except Exception as e:
                print(f"Error loading provider {provider_name}: {e}")
                continue

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading providers: {str(e)}")


@app.get("/api/models/default")
async def get_default_model() -> Dict[str, Any]:
    """Get default model configuration."""
    try:
        model_factory = get_model_factory()

        # Get default provider (aicloud_glm45 if available)
        default_provider = "aicloud_glm45"
        if default_provider not in model_factory.list_providers():
            default_provider = model_factory.list_providers()[0] if model_factory.list_providers() else "aicloud_glm45"

        provider = model_factory.get_provider(default_provider)
        default_model = provider.get_default_model("query_generator") or provider.list_available_models()[0]

        return {
            "model": f"{default_provider}/{default_model}",
            "provider": default_provider,
            "modelName": default_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting default model: {str(e)}")


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
