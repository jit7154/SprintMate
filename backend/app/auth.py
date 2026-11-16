from collections.abc import Callable

from fastapi import Header, HTTPException, status


class UserContext:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role.lower()

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"


async def get_current_user(
    x_user_role: str = Header(default="manager", alias="X-User-Role"),
    x_user_id: str = Header(default="manager-alex", alias="X-User-Id"),
) -> UserContext:
    """Extract authenticated demo user context from request headers."""
    normalized_role = x_user_role.strip().lower()
    if normalized_role not in {"manager", "developer"}:
        normalized_role = "developer"
    return UserContext(user_id=x_user_id.strip(), role=normalized_role)


def require_role(allowed_role: str) -> Callable:
    """Dependency that ensures caller has the exact authorized role."""

    async def role_checker(
        user: UserContext = get_current_user,
    ) -> UserContext:
        if user.role != allowed_role.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{allowed_role}' role. Current role is '{user.role}'.",
            )
        return user

    return role_checker
