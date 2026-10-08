"""
Pagination helpers.
"""
from typing import Sequence, TypeVar
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def paginate(
    db: AsyncSession,
    stmt: Select,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, int]:
    """Paginate a SELECT statement.

    Returns (items, total).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20

    skip = (page - 1) * page_size

    count_stmt = select(func.count()).select_from(
        stmt.order_by(None).subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    result = await db.execute(stmt.offset(skip).limit(page_size))
    return list(result.scalars().all()), total