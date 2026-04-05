"""
Authentication Routes
Login, Register, Verify, Logout
"""
from fastapi import APIRouter, Request, Response, HTTPException, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from config import settings
from models import User, UserRole, LoginLog, LoginStatus
from utils.password import verify_password, validate_password_strength
from utils.jwt import create_token, verify_token
from utils.detection import send_login_event, send_registration_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


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


@router.post("/register")
async def register(request: Request, data: RegisterRequest):
    """Register new user"""
    ip_address = get_client_ip(request)

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

    # Create user (default role is USER for public registration)
    user = await User.create(
        username=data.username,
        email=data.email,
        password=data.password,
        role=UserRole.USER  # Force USER role for public registration
    )

    # Send to detection
    await send_registration_event(
        username=data.username,
        email=data.email,
        ip_address=ip_address,
        role="USER"
    )

    logger.info(f"New user registered: {data.username}")

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
