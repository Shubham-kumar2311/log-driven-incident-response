"""
Client Service Auth Middleware
================================================================================
COPY THIS FILE to other services (localhost:3000, 3001, 3002) to integrate
with the Central Auth Server.

This provides:
1. JWT verification from cookies
2. Role-based access control
3. Auto-redirect to login page if not authenticated
================================================================================
"""
from functools import wraps
from typing import Optional, List
import jwt
import httpx


# ============================================================
# CONFIGURATION - ADJUST FOR YOUR SERVICE
# ============================================================

AUTH_SERVER_URL = "http://localhost:8000"
JWT_SECRET = "super-secret-key-change-in-production"  # Must match auth server
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "auth_token"

# Role this service requires (set based on service)
# USER UI (3000) -> "USER"
# ANALYST UI (3001) -> "ANALYST"
# ADMIN UI (3002) -> "ADMIN"
REQUIRED_ROLE = "USER"  # Change this per service

# Paths that don't require authentication
EXCLUDE_PATHS = [
    "/health",
    "/docs",
    "/openapi.json",
    "/favicon.ico"
]


# ============================================================
# JWT VERIFICATION
# ============================================================

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token locally"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


async def verify_token_remote(token: str) -> Optional[dict]:
    """Verify token by calling auth server's /verify endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_SERVER_URL}/verify",
                cookies={COOKIE_NAME: token}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated"):
                    return data.get("user")
            return None
    except Exception:
        return None


# ============================================================
# FASTAPI MIDDLEWARE & DEPENDENCIES
# ============================================================

# For FastAPI services
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse


async def get_current_user(request: Request) -> Optional[dict]:
    """Extract user from JWT cookie"""
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    return {
        "id": payload.get("user_id"),
        "role": payload.get("role")
    }


async def require_auth(request: Request) -> dict:
    """Require authentication - redirects to login if not authenticated"""
    user = await get_current_user(request)

    if not user:
        # Redirect to auth server login
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"{AUTH_SERVER_URL}/login"}
        )

    return user


def require_role(allowed_roles: List[str]):
    """Require specific roles"""
    async def checker(request: Request) -> dict:
        user = await require_auth(request)

        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )

        return user

    return checker


class AuthMiddlewareASGI:
    """
    ASGI Middleware to protect entire service.
    Add to FastAPI app:
        app.add_middleware(AuthMiddlewareASGI, required_role="ANALYST")
    """

    def __init__(self, app, required_role: str = None, exclude_paths: List[str] = None):
        self.app = app
        self.required_role = required_role
        self.exclude_paths = exclude_paths or EXCLUDE_PATHS

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

        # Get cookies from scope
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()

        # Parse cookies
        cookies = {}
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    key, value = item.strip().split("=", 1)
                    cookies[key] = value

        token = cookies.get(COOKIE_NAME)

        if not token:
            # Redirect to login
            response = RedirectResponse(
                url=f"{AUTH_SERVER_URL}/login",
                status_code=307
            )
            await response(scope, receive, send)
            return

        payload = verify_token(token)

        if not payload:
            response = RedirectResponse(
                url=f"{AUTH_SERVER_URL}/login",
                status_code=307
            )
            await response(scope, receive, send)
            return

        # Check role if required
        if self.required_role:
            user_role = payload.get("role")

            # Role hierarchy: ADMIN > ANALYST > USER
            role_levels = {"USER": 1, "ANALYST": 2, "ADMIN": 3}
            required_level = role_levels.get(self.required_role, 0)
            user_level = role_levels.get(user_role, 0)

            if user_level < required_level:
                from fastapi.responses import JSONResponse
                response = JSONResponse(
                    status_code=403,
                    content={"error": f"Access denied. Required role: {self.required_role}"}
                )
                await response(scope, receive, send)
                return

        # Add user to request state
        scope["state"] = scope.get("state", {})
        scope["state"]["user"] = payload

        await self.app(scope, receive, send)


# ============================================================
# FLASK MIDDLEWARE (if using Flask)
# ============================================================

def flask_auth_required(f):
    """
    Flask decorator for auth-required routes.

    Usage:
        @app.route('/protected')
        @flask_auth_required
        def protected():
            return 'Hello, authenticated user!'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, redirect, g

        token = request.cookies.get(COOKIE_NAME)

        if not token:
            return redirect(f"{AUTH_SERVER_URL}/login")

        payload = verify_token(token)

        if not payload:
            return redirect(f"{AUTH_SERVER_URL}/login")

        g.user = payload
        return f(*args, **kwargs)

    return decorated_function


def flask_role_required(allowed_roles: List[str]):
    """
    Flask decorator for role-required routes.

    Usage:
        @app.route('/admin')
        @flask_role_required(['ADMIN'])
        def admin():
            return 'Hello, admin!'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, redirect, jsonify, g

            token = request.cookies.get(COOKIE_NAME)

            if not token:
                return redirect(f"{AUTH_SERVER_URL}/login")

            payload = verify_token(token)

            if not payload:
                return redirect(f"{AUTH_SERVER_URL}/login")

            if payload.get("role") not in allowed_roles:
                return jsonify({"error": "Access denied"}), 403

            g.user = payload
            return f(*args, **kwargs)

        return decorated_function
    return decorator


# ============================================================
# EXPRESS.JS MIDDLEWARE (JavaScript example)
# ============================================================

EXPRESS_MIDDLEWARE_EXAMPLE = '''
// auth-middleware.js - For Express.js services

const jwt = require('jsonwebtoken');

const AUTH_SERVER_URL = 'http://localhost:8000';
const JWT_SECRET = 'super-secret-key-change-in-production';
const COOKIE_NAME = 'auth_token';

// Verify JWT token
function verifyToken(token) {
    try {
        return jwt.verify(token, JWT_SECRET);
    } catch (err) {
        return null;
    }
}

// Auth middleware
function requireAuth(req, res, next) {
    const token = req.cookies[COOKIE_NAME];

    if (!token) {
        return res.redirect(`${AUTH_SERVER_URL}/login`);
    }

    const payload = verifyToken(token);

    if (!payload) {
        return res.redirect(`${AUTH_SERVER_URL}/login`);
    }

    req.user = payload;
    next();
}

// Role middleware
function requireRole(allowedRoles) {
    return (req, res, next) => {
        if (!req.user) {
            return res.redirect(`${AUTH_SERVER_URL}/login`);
        }

        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({ error: 'Access denied' });
        }

        next();
    };
}

module.exports = { requireAuth, requireRole, verifyToken };

// Usage in Express app:
// const { requireAuth, requireRole } = require('./auth-middleware');
// app.use(requireAuth);  // Protect all routes
// app.get('/admin', requireRole(['ADMIN']), (req, res) => { ... });
'''


# ============================================================
# USAGE EXAMPLES
# ============================================================

USAGE_EXAMPLE = '''
# ============================================================
# FASTAPI SERVICE EXAMPLE (e.g., User UI on port 3000)
# ============================================================

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse

# Import this middleware file
from client_auth_middleware import AuthMiddlewareASGI, get_current_user, require_auth

app = FastAPI()

# Option 1: Protect entire app with middleware
app.add_middleware(AuthMiddlewareASGI, required_role="USER")

# Option 2: Protect individual routes
@app.get("/dashboard")
async def dashboard(user: dict = Depends(require_auth)):
    return {"message": f"Hello {user['role']}!", "user_id": user["id"]}

# Get current user without requiring auth
@app.get("/public")
async def public(request: Request):
    user = await get_current_user(request)
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False}


# ============================================================
# SERVICE-SPECIFIC CONFIGURATIONS
# ============================================================

# USER UI (port 3000):
#   REQUIRED_ROLE = "USER"
#   Any role (USER, ANALYST, ADMIN) can access

# ANALYST UI (port 3001):
#   REQUIRED_ROLE = "ANALYST"
#   Only ANALYST and ADMIN can access

# ADMIN UI (port 3002):
#   REQUIRED_ROLE = "ADMIN"
#   Only ADMIN can access
'''


if __name__ == "__main__":
    print("Client Auth Middleware")
    print("=" * 60)
    print("Copy this file to your service and import the middleware.")
    print("")
    print("FastAPI usage:")
    print("  app.add_middleware(AuthMiddlewareASGI, required_role='USER')")
    print("")
    print("Flask usage:")
    print("  @flask_auth_required")
    print("  def protected_route():")
    print("      ...")
