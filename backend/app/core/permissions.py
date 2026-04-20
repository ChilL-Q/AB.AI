from enum import StrEnum
from typing import Any

from app.core.exceptions import ForbiddenError


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MECHANIC = "mechanic"


# Role hierarchy: higher index = more permissions
_ROLE_RANK: dict[Role, int] = {
    Role.MECHANIC: 0,
    Role.MANAGER: 1,
    Role.ADMIN: 2,
    Role.OWNER: 3,
}


def require_role(*roles: Role):
    """FastAPI dependency factory — raises 403 if current user's role is not in allowed list."""

    def _check(current_user: Any) -> None:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"Role '{current_user.role}' is not allowed. Required: {[r.value for r in roles]}"
            )

    return _check


def has_role(user_role: str, *roles: Role) -> bool:
    return Role(user_role) in roles


def has_min_role(user_role: str, min_role: Role) -> bool:
    return _ROLE_RANK.get(Role(user_role), -1) >= _ROLE_RANK[min_role]
