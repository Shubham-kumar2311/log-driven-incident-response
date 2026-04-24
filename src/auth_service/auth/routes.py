"""
Authentication Routes
Login, Register, Verify, Logout
"""
from fastapi import APIRouter, Request, Response, HTTPException, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, quote_plus
import logging
import re
import secrets

import httpx

from config import settings
from models import User, UserRole, LoginLog, LoginStatus
from utils.password import verify_password, validate_password_strength
from utils.jwt import create_token, verify_token
from utils.detection import send_login_event, send_registration_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

IIITG_ANALYST_DOMAIN = "iiitg.ac.in"


# ============================================================
# REQUEST MODELS
# ============================================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[UserRole] = UserRole.USER


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


def set_auth_cookie(response: Response, token: str) -> None:
    """Set authentication cookie"""
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/"
    )


def delete_auth_cookie(response: Response) -> None:
    """Delete authentication cookie"""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/"
    )


def _oauth_state_cookie_name(provider: str) -> str:
    return f"oauth_state_{provider}"


def _set_oauth_state_cookie(response: Response, provider: str, state_value: str) -> None:
    response.set_cookie(
        key=_oauth_state_cookie_name(provider),
        value=state_value,
        max_age=settings.OAUTH_STATE_COOKIE_MAX_AGE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )


def _delete_oauth_state_cookie(response: Response, provider: str) -> None:
    response.delete_cookie(key=_oauth_state_cookie_name(provider), path="/")


def _oauth_error_redirect(message: str, provider: Optional[str] = None) -> RedirectResponse:
    query = quote_plus(message)
    target = f"/login?error={query}"
    if provider:
        target = f"{target}&provider={quote_plus(provider)}"
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


def _is_provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)
    if provider == "github":
        return bool(settings.GITHUB_OAUTH_CLIENT_ID and settings.GITHUB_OAUTH_CLIENT_SECRET)
    return False


def _resolve_redirect_uri(request: Request, provider: str) -> str:
    if provider == "google":
        if settings.GOOGLE_OAUTH_REDIRECT_URI.strip():
            return settings.GOOGLE_OAUTH_REDIRECT_URI.strip()
        return str(request.url_for("oauth_google_callback"))

    if settings.GITHUB_OAUTH_REDIRECT_URI.strip():
        return settings.GITHUB_OAUTH_REDIRECT_URI.strip()
    return str(request.url_for("oauth_github_callback"))


def _normalize_username_seed(raw: str) -> str:
    candidate = re.sub(r"[^a-z0-9._-]", "", raw.lower().strip())
    candidate = candidate.strip("._-")
    return candidate or "user"


async def _build_unique_username(seed: str) -> str:
    base = _normalize_username_seed(seed)
    if not await User.exists_by_username(base):
        return base

    suffix = 1
    while suffix < 10000:
        candidate = f"{base}{suffix}"
        if not await User.exists_by_username(candidate):
            return candidate
        suffix += 1

    return f"{base}{secrets.randbelow(999999)}"


def _oauth_default_role() -> UserRole:
    configured = settings.OAUTH_DEFAULT_ROLE.upper().strip()
    try:
        return UserRole(configured)
    except ValueError:
        return UserRole.USER


def _is_analyst_email_domain(email: str) -> bool:
    normalized = email.lower().strip()
    return normalized.endswith(f"@{IIITG_ANALYST_DOMAIN}")


def _oauth_role_for_email(email: str) -> UserRole:
    if _is_analyst_email_domain(email):
        return UserRole.ANALYST
    return _oauth_default_role()


async def _ensure_iiitg_role_for_user(
    user: Optional[Dict[str, Any]],
    email: str,
) -> Optional[Dict[str, Any]]:
    if not user or not _is_analyst_email_domain(email):
        return user

    current_role = user.get("role")
    if current_role in {UserRole.ANALYST.value, UserRole.ADMIN.value}:
        return user

    updated = await User.update_role(user["id"], UserRole.ANALYST.value)
    return updated or user


def _build_google_authorize_url(request: Request, state_value: str) -> str:
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": _resolve_redirect_uri(request, "google"),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state_value,
        "access_type": "online",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _build_github_authorize_url(request: Request, state_value: str) -> str:
    params = {
        "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
        "redirect_uri": _resolve_redirect_uri(request, "github"),
        "scope": "read:user user:email",
        "state": state_value,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


def _pick_github_email(profile: Dict[str, Any], emails: list) -> Optional[str]:
    if profile.get("email"):
        return profile["email"]

    for email_obj in emails:
        if email_obj.get("primary") and email_obj.get("verified"):
            return email_obj.get("email")

    for email_obj in emails:
        if email_obj.get("verified"):
            return email_obj.get("email")

    if emails:
        return emails[0].get("email")
    return None


async def _exchange_google_code(code: str, request: Request) -> Dict[str, Any]:
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": _resolve_redirect_uri(request, "google"),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)

    if response.status_code >= 400:
        raise ValueError("Google token exchange failed")

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("Google access token missing")

    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if profile_response.status_code >= 400:
        raise ValueError("Google profile lookup failed")

    profile = profile_response.json()
    oauth_sub = str(profile.get("sub", "")).strip()
    email = str(profile.get("email", "")).lower().strip()
    if not oauth_sub or not email:
        raise ValueError("Google profile did not include required identity fields")

    preferred_username = profile.get("name") or email.split("@")[0]

    return {
        "oauth_sub": oauth_sub,
        "email": email,
        "preferred_username": preferred_username,
        "avatar_url": profile.get("picture"),
    }


async def _exchange_github_code(code: str, request: Request) -> Dict[str, Any]:
    payload = {
        "code": code,
        "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
        "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
        "redirect_uri": _resolve_redirect_uri(request, "github"),
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(GITHUB_TOKEN_URL, data=payload, headers=headers)

    if token_response.status_code >= 400:
        raise ValueError("GitHub token exchange failed")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("GitHub access token missing")

    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_response = await client.get(GITHUB_USER_URL, headers=api_headers)
        emails_response = await client.get(GITHUB_EMAILS_URL, headers=api_headers)

    if profile_response.status_code >= 400:
        raise ValueError("GitHub profile lookup failed")

    profile = profile_response.json()
    emails_data = emails_response.json() if emails_response.status_code < 400 else []

    oauth_sub = str(profile.get("id", "")).strip()
    email = _pick_github_email(profile, emails_data)
    if not oauth_sub or not email:
        raise ValueError("GitHub profile did not include required identity fields")

    preferred_username = profile.get("login") or profile.get("name") or email.split("@")[0]

    return {
        "oauth_sub": oauth_sub,
        "email": email.lower().strip(),
        "preferred_username": preferred_username,
        "avatar_url": profile.get("avatar_url"),
    }


async def _resolve_or_create_oauth_user(
    provider: str,
    oauth_sub: str,
    email: str,
    preferred_username: str,
    avatar_url: Optional[str],
) -> Dict[str, Any]:
    existing_by_oauth = await User.find_by_oauth_key(provider, oauth_sub)
    if existing_by_oauth:
        return await _ensure_iiitg_role_for_user(existing_by_oauth, email)

    existing_by_email = await User.find_by_email(email)
    if existing_by_email:
        linked = await User.link_oauth_account(
            existing_by_email["id"],
            provider=provider,
            oauth_sub=oauth_sub,
            avatar_url=avatar_url,
        )
        return await _ensure_iiitg_role_for_user(linked or existing_by_email, email)

    username = await _build_unique_username(preferred_username or email.split("@")[0])
    return await User.create_oauth_user(
        username=username,
        email=email,
        provider=provider,
        oauth_sub=oauth_sub,
        avatar_url=avatar_url,
        role=_oauth_role_for_email(email),
    )


async def _finalize_oauth_login(
    request: Request,
    provider: str,
    oauth_sub: str,
    email: str,
    preferred_username: str,
    avatar_url: Optional[str],
) -> Tuple[RedirectResponse, Dict[str, Any]]:
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    user = await _resolve_or_create_oauth_user(
        provider=provider,
        oauth_sub=oauth_sub,
        email=email,
        preferred_username=preferred_username,
        avatar_url=avatar_url,
    )

    if not user.get("is_active"):
        raise ValueError("Account is deactivated")

    is_new_ip = await LoginLog.is_new_ip_for_user(user["id"], ip_address)
    await LoginLog.create(
        user_id=user["id"],
        username_attempted=user["username"],
        ip_address=ip_address,
        status=LoginStatus.SUCCESS,
        user_agent=user_agent,
    )

    await User.update_last_login(user["id"], ip_address)

    await send_login_event(
        username=user["username"],
        ip_address=ip_address,
        success=True,
        user_id=user["id"],
        user_agent=user_agent,
        is_new_ip=is_new_ip,
    )

    token = create_token(user["id"], user["role"])
    redirect_url = settings.ROLE_REDIRECTS.get(user["role"], settings.ROLE_REDIRECTS["USER"])
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    set_auth_cookie(response, token)
    return response, user


async def get_authenticated_user(request: Request) -> Optional[dict]:
    """Get authenticated user from auth cookie"""
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


async def require_admin_user(request: Request) -> dict:
    """Require admin session for privileged actions"""
    user = await get_authenticated_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# ============================================================
# ROUTES
# ============================================================

@router.post("/login")

async def login(request: Request, data: LoginRequest):
    """
    Authenticate user and set JWT cookie.
    Returns redirect URL based on role.
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Find user
    user = await User.find_by_username_or_email(data.username)

    if not user:
        # Log failed attempt
        await LoginLog.create(
            user_id=None,
            username_attempted=data.username,
            ip_address=ip_address,
            status=LoginStatus.FAILED,
            user_agent=user_agent,
            failure_reason="User not found"
        )

        # Get failed attempts count
        failed_count = await LoginLog.get_recent_failed_by_ip(
            ip_address,
            settings.BRUTE_FORCE_WINDOW_SECONDS
        )

        # Send to detection
        await send_login_event(
            username=data.username,
            ip_address=ip_address,
            success=False,
            user_agent=user_agent,
            failed_attempts=failed_count
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if active
    if not user.get("is_active"):
        await LoginLog.create(
            user_id=user["id"],
            username_attempted=data.username,
            ip_address=ip_address,
            status=LoginStatus.FAILED,
            user_agent=user_agent,
            failure_reason="Account deactivated"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    if not user.get("password_hash"):
        await LoginLog.create(
            user_id=user["id"],
            username_attempted=data.username,
            ip_address=ip_address,
            status=LoginStatus.FAILED,
            user_agent=user_agent,
            failure_reason="Password login attempted for OAuth account"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use social sign-in for this account"
        )

    # Verify password
    if not verify_password(data.password, user["password_hash"]):
        await LoginLog.create(
            user_id=user["id"],
            username_attempted=data.username,
            ip_address=ip_address,
            status=LoginStatus.FAILED,
            user_agent=user_agent,
            failure_reason="Invalid password"
        )

        failed_count = await LoginLog.get_recent_failed_by_ip(
            ip_address,
            settings.BRUTE_FORCE_WINDOW_SECONDS
        )

        await send_login_event(
            username=data.username,
            ip_address=ip_address,
            success=False,
            user_id=user["id"],
            user_agent=user_agent,
            failed_attempts=failed_count
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if new IP
    is_new_ip = await LoginLog.is_new_ip_for_user(user["id"], ip_address)

    # Log successful login
    await LoginLog.create(
        user_id=user["id"],
        username_attempted=data.username,
        ip_address=ip_address,
        status=LoginStatus.SUCCESS,
        user_agent=user_agent
    )

    # Update last login
    await User.update_last_login(user["id"], ip_address)

    # Send to detection
    await send_login_event(
        username=data.username,
        ip_address=ip_address,
        success=True,
        user_id=user["id"],
        user_agent=user_agent,
        is_new_ip=is_new_ip
    )

    # Create JWT token
    token = create_token(user["id"], user["role"])

    # Get redirect URL based on role
    redirect_url = settings.ROLE_REDIRECTS.get(user["role"], settings.ROLE_REDIRECTS["USER"])

    logger.info(f"User logged in: {user['username']} ({user['role']}) from {ip_address}")

    # Return response with cookie
    response = JSONResponse(content={
        "success": True,
        "message": "Login successful",
        "redirect_url": redirect_url,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    })

    set_auth_cookie(response, token)
    return response


@router.post("/login/form")
async def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Form-based login endpoint.
    Redirects to appropriate UI after success.
    """
    data = LoginRequest(username=username, password=password)

    try:
        # Reuse login logic
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        user = await User.find_by_username_or_email(data.username)

        if not user or not user.get("is_active"):
            return RedirectResponse(
                url="/login?error=Invalid+credentials",
                status_code=status.HTTP_303_SEE_OTHER
            )

        if not user.get("password_hash"):
            return RedirectResponse(
                url="/login?error=Use+social+sign-in+for+this+account",
                status_code=status.HTTP_303_SEE_OTHER
            )

        if not verify_password(data.password, user["password_hash"]):
            await LoginLog.create(
                user_id=user["id"] if user else None,
                username_attempted=data.username,
                ip_address=ip_address,
                status=LoginStatus.FAILED,
                user_agent=user_agent,
                failure_reason="Invalid password"
            )

            failed_count = await LoginLog.get_recent_failed_by_ip(
                ip_address,
                settings.BRUTE_FORCE_WINDOW_SECONDS
            )

            await send_login_event(
                username=data.username,
                ip_address=ip_address,
                success=False,
                user_id=user["id"] if user else None,
                user_agent=user_agent,
                failed_attempts=failed_count
            )

            return RedirectResponse(
                url="/login?error=Invalid+credentials",
                status_code=status.HTTP_303_SEE_OTHER
            )

        # Check if new IP
        is_new_ip = await LoginLog.is_new_ip_for_user(user["id"], ip_address)

        # Log success
        await LoginLog.create(
            user_id=user["id"],
            username_attempted=data.username,
            ip_address=ip_address,
            status=LoginStatus.SUCCESS,
            user_agent=user_agent
        )

        await User.update_last_login(user["id"], ip_address)

        await send_login_event(
            username=data.username,
            ip_address=ip_address,
            success=True,
            user_id=user["id"],
            user_agent=user_agent,
            is_new_ip=is_new_ip
        )

        # Create token
        token = create_token(user["id"], user["role"])

        # Redirect based on role
        redirect_url = settings.ROLE_REDIRECTS.get(user["role"], settings.ROLE_REDIRECTS["USER"])

        logger.info(f"User logged in via form: {user['username']} -> {redirect_url}")

        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_303_SEE_OTHER
        )

        set_auth_cookie(response, token)
        return response

    except Exception as e:
        logger.error(f"Login form error: {e}")
        return RedirectResponse(
            url="/login?error=Login+failed",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.get("/oauth/google/login")
async def oauth_google_login(request: Request):
    """Redirect user to Google OAuth consent page"""
    if not _is_provider_configured("google"):
        return _oauth_error_redirect("Google OAuth is not configured", "google")

    state_value = secrets.token_urlsafe(32)
    auth_url = _build_google_authorize_url(request, state_value)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    _set_oauth_state_cookie(response, "google", state_value)
    return response


@router.get("/oauth/google/callback")
async def oauth_google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Google OAuth callback and create local auth session"""
    provider = "google"

    if not _is_provider_configured(provider):
        return _oauth_error_redirect("Google OAuth is not configured", provider)

    if error:
        response = _oauth_error_redirect("Google sign-in was cancelled", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    expected_state = request.cookies.get(_oauth_state_cookie_name(provider))
    if not state or not expected_state or state != expected_state:
        response = _oauth_error_redirect("Invalid OAuth state. Please retry sign-in.", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    if not code:
        response = _oauth_error_redirect("Google callback is missing authorization code", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    try:
        profile = await _exchange_google_code(code, request)
        response, user = await _finalize_oauth_login(
            request=request,
            provider=provider,
            oauth_sub=profile["oauth_sub"],
            email=profile["email"],
            preferred_username=profile["preferred_username"],
            avatar_url=profile.get("avatar_url"),
        )
        _delete_oauth_state_cookie(response, provider)
        logger.info("OAuth login successful: provider=%s user=%s", provider, user["username"])
        return response
    except Exception as exc:
        logger.warning("Google OAuth callback failed: %s", exc)
        response = _oauth_error_redirect("Google sign-in failed. Please try again.", provider)
        _delete_oauth_state_cookie(response, provider)
        return response


@router.get("/oauth/github/login")
async def oauth_github_login(request: Request):
    """Redirect user to GitHub OAuth consent page"""
    if not _is_provider_configured("github"):
        return _oauth_error_redirect("GitHub OAuth is not configured", "github")

    state_value = secrets.token_urlsafe(32)
    auth_url = _build_github_authorize_url(request, state_value)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    _set_oauth_state_cookie(response, "github", state_value)
    return response


@router.get("/oauth/github/callback")
async def oauth_github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle GitHub OAuth callback and create local auth session"""
    provider = "github"

    if not _is_provider_configured(provider):
        return _oauth_error_redirect("GitHub OAuth is not configured", provider)

    if error:
        response = _oauth_error_redirect("GitHub sign-in was cancelled", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    expected_state = request.cookies.get(_oauth_state_cookie_name(provider))
    if not state or not expected_state or state != expected_state:
        response = _oauth_error_redirect("Invalid OAuth state. Please retry sign-in.", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    if not code:
        response = _oauth_error_redirect("GitHub callback is missing authorization code", provider)
        _delete_oauth_state_cookie(response, provider)
        return response

    try:
        profile = await _exchange_github_code(code, request)
        response, user = await _finalize_oauth_login(
            request=request,
            provider=provider,
            oauth_sub=profile["oauth_sub"],
            email=profile["email"],
            preferred_username=profile["preferred_username"],
            avatar_url=profile.get("avatar_url"),
        )
        _delete_oauth_state_cookie(response, provider)
        logger.info("OAuth login successful: provider=%s user=%s", provider, user["username"])
        return response
    except Exception as exc:
        logger.warning("GitHub OAuth callback failed: %s", exc)
        response = _oauth_error_redirect("GitHub sign-in failed. Please try again.", provider)
        _delete_oauth_state_cookie(response, provider)
        return response


@router.post("/register")
async def register(request: Request, data: RegisterRequest):
    """Register new user"""
    ip_address = get_client_ip(request)
    assigned_role = UserRole.ANALYST if _is_analyst_email_domain(str(data.email)) else UserRole.USER

    # Validate password
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check username exists
    if await User.exists_by_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # Check email exists
    if await User.exists_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Create user and auto-upgrade domain-based analyst accounts
    user = await User.create(
        username=data.username,
        email=data.email,
        password=data.password,
        role=assigned_role
    )

    # Send to detection
    await send_registration_event(
        username=data.username,
        email=data.email,
        ip_address=ip_address,
        role=assigned_role.value
    )

    logger.info(f"New user registered: {data.username} ({assigned_role.value})")

    return {
        "success": True,
        "message": "Registration successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }


@router.get("/verify")
async def verify(request: Request):
    """
    Verify authentication token from cookie.
    Returns user info if valid.
    """
    token = request.cookies.get(settings.COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("user_id")
    user = await User.find_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated"
        )

    return {
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }


@router.get("/admin/users")
async def admin_list_users(
    request: Request,
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None
):
    """Admin-only user search (username/email) with pagination"""
    await require_admin_user(request)

    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be >= 1")

    if not search or not search.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query is required. Search by username or email."
        )

    safe_limit = max(1, min(limit, 100))
    users_data = await User.find_all(page=page, limit=safe_limit, search=search.strip())

    return {
        "success": True,
        "data": users_data
    }


@router.patch("/admin/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    data: UpdateUserRoleRequest,
    request: Request
):
    """Admin-only role update endpoint"""
    admin_user = await require_admin_user(request)

    target_user = await User.find_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if target_user["id"] == admin_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )

    current_role = target_user.get("role")
    next_role = data.role.value

    if current_role == UserRole.ADMIN.value and next_role != UserRole.ADMIN.value:
        admin_count = await User.count_by_role(UserRole.ADMIN.value)
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one admin account must remain"
            )

    updated_user = await User.update_role(
        user_id=user_id,
        new_role=next_role,
        updated_by=admin_user["id"]
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )

    logger.info(
        "Admin role update: admin=%s target=%s old_role=%s new_role=%s",
        admin_user["username"],
        target_user["username"],
        current_role,
        next_role,
    )

    return {
        "success": True,
        "message": "User role updated successfully",
        "user": updated_user
    }


@router.post("/logout")
async def logout(request: Request):
    """Logout user by clearing cookie"""
    response = JSONResponse(content={
        "success": True,
        "message": "Logged out successfully"
    })

    delete_auth_cookie(response)
    return response


@router.get("/logout")
async def logout_redirect(request: Request):
    """Logout and redirect to login page"""
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )

    delete_auth_cookie(response)
    return response
