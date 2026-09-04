"""Knowledge graph domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class KnowledgeGraphError(ApplicationError):
    """Base knowledge-graph failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "KNOWLEDGE_GRAPH_ERROR"


class GraphNotFoundError(ApplicationError):
    """Raised when a knowledge graph run cannot be located."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "KNOWLEDGE_GRAPH_NOT_FOUND"


class EntityNotFoundError(ApplicationError):
    """Raised when a graph entity cannot be located."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "GRAPH_ENTITY_NOT_FOUND"
