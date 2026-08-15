"""Basic checks that confirm the initial application packages can be imported."""

import importlib
import logging

from app.logging import configure_logging


APPLICATION_MODULES = (
    "app.frontend.streamlit_app", "app.backend.main", "app.backend.schemas",
    "app.agent.graph", "app.agent.state", "app.agent.prompts", "app.agent.nodes", "app.agent.tools",
    "app.rag.loaders", "app.rag.chunking", "app.rag.embeddings", "app.rag.vectorstore", "app.rag.retriever",
    "app.database.connection", "app.database.models", "app.database.queries", "app.database.seed",
    "app.market_data.client", "app.market_data.service",
)


def check_application_imports() -> bool:
    """Import every Phase 1 module and return whether all imports succeeded."""
    for module_name in APPLICATION_MODULES:
        importlib.import_module(module_name)
    return True


def main() -> None:
    """Run the health check from the command line."""
    configure_logging()
    check_application_imports()
    logging.getLogger(__name__).info("Health check passed: all application modules import correctly.")


if __name__ == "__main__":
    main()
