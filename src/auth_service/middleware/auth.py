"""
Authentication Middleware
JWT verification and role-based access control
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import List, Optional, Callable
from functools import wraps

from config import settings
from utils.jwt import verify_token
from models import User, UserRole


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and verify user from JWT cookie.
    Returns user dict or None.
    """
    token = request.cookies.get(settings.COOKIE_NAME)

    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    user = await User.find_by_id(user_id)
    if not user or not user.get("is_active"):
        return None

    return user


async def require_auth(request: Request) -> dict:
    """
    Require authentication.
    Raises 401 or redirects to login if not authenticated.
    """
    user = await get_current_user(request)

    if not user:
        # Check if it's an API request or browser request
        accept = request.headers.get("Accept", "")
        if "application/json" in accept:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        else:
            # Redirect to login page
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": f"{settings.CORS_ORIGINS[-1]}/login"}
            )

    return user


def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """
    async def role_checker(request: Request) -> dict:
        user = await require_auth(request)

        user_role = user.get("role")
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not found"
            )

        try:
            user_role_enum = UserRole(user_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )

        if user_role_enum not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )

        return user

    return role_checker


def require_admin():
    """Shortcut for admin-only access"""
    return require_roles(UserRole.ADMIN)


def require_analyst_or_admin():
    """Shortcut for analyst or admin access"""
    return require_roles(UserRole.ADMIN, UserRole.ANALYST)


def require_any_role():
    """Shortcut for any authenticated user"""
    return require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.USER)


class AuthMiddleware:
    """
    ASGI Middleware for authentication.
    Redirects unauthenticated requests to login.
    """

    def __init__(self, app, exclude_paths: List[str] = None):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/login",
            "/register",
            "/verify",
            "/logout",
            "/health",
            "/docs",
            "/openapi.json",
            "/static",
            "/favicon.ico"
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        # Skip excluded paths
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                await self.app(scope, receive, send)
                return

        # Check authentication
        from starlette.requests import Request
        request = Request(scope, receive)

        token = request.cookies.get(settings.COOKIE_NAME)

        if not token:
            # Redirect to login
            response = RedirectResponse(
                url=f"http://localhost:{settings.PORT}/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )
            await response(scope, receive, send)
            return

        payload = verify_token(token)
        if not payload:
            response = RedirectResponse(
                url=f"http://localhost:{settings.PORT}/login",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )
            await response(scope, receive, send)
            return

        # Token is valid, proceed
        await self.app(scope, receive, send)
