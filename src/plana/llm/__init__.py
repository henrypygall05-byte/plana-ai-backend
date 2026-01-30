"""
LLM client interfaces.

Provides abstraction over different LLM providers (Anthropic, OpenAI).
Set PLANA_SKIP_LLM=true to use stub responses for offline development.
"""

from plana.llm.stub_client import StubLLMClient

__all__ = ["LLMClient", "StubLLMClient", "get_llm_client"]


def get_llm_client():
    """
    Get the appropriate LLM client based on configuration.

    Returns StubLLMClient if PLANA_SKIP_LLM=true, otherwise real LLMClient.
    """
    from plana.config import get_settings

    settings = get_settings()

    if settings.skip_llm:
        return StubLLMClient()

    # Check if API keys are configured
    if not settings.llm.anthropic_api_key and not settings.llm.openai_api_key:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.warning("No LLM API keys configured, using stub client")
        return StubLLMClient()

    from plana.llm.client import LLMClient
    return LLMClient()


# Lazy import for backwards compatibility
def __getattr__(name):
    if name == "LLMClient":
        from plana.llm.client import LLMClient
        return LLMClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
