import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RoleService:
    def __init__(self):
        pass

    async def role_pagination(
        self,
        db: Session,
        page: int,
        limit: int,
    ) -> dict[str, Any]:
        return {
            "roleList": [],
            "total": 0,
            "limit": limit,
            "page": page,
        }
