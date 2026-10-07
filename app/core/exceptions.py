"""Domain-level exceptions."""

class DomainError(Exception):
    """Base for domain-level errors."""


class TopicNameAlreadyExistsError(DomainError):
    """Raised when a topic name is already taken for the user."""


class TopicNotFoundError(DomainError):
    """Raised when a topic is not found."""