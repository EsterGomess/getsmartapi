"""
Pagination schemas.
"""


from app.schemas.base import BaseSchema

class PaginationMeta(BaseSchema):
    """Metadata for paginated responses."""
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseSchema):
    """Generic wrapper for paginated responses."""
    pagination: PaginationMeta
