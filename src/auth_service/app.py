"""
Central Authentication Server
Main FastAPI Application
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import logging
import sys
from urllib.parse import quote_plus

from config import settings
from database import Database
from auth import auth_router
from models import User, UserRole
from utils.jwt import verify_token

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ============================================================
# APP LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Central Auth Server...")
    await Database.connect()
    logger.info(f"Auth Server running on http://localhost:{settings.PORT}")

    yield

    # Shutdown
    logger.info("Shutting down Auth Server...")
    await Database.disconnect()


# ============================================================
# CREATE APP
# ============================================================

app = FastAPI(
    title="Central Auth Server",
    description="Authentication system for Incident Response Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ============================================================
# TEMPLATES & STATIC FILES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount static files if directory exists
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


async def _get_current_user_from_request(request: Request):
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


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


# ============================================================
# ROUTES
# ============================================================

# Include auth routes
app.include_router(auth_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Serve registration page"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/access-denied", response_class=HTMLResponse)
async def access_denied_page(request: Request):
    """Friendly page for role-based access denials"""
    current_user = await _get_current_user_from_request(request)
    required_role = request.query_params.get("required_role", "UNKNOWN")
    current_role = request.query_params.get("current_role", "UNKNOWN")
    target = request.query_params.get("target", "/")
    return templates.TemplateResponse(
        "access_denied.html",
        {
            "request": request,
            "required_role": required_role,
            "current_role": current_role,
            "username": current_user.get("username") if current_user else None,
            "target": target,
        },
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel_page(request: Request):
    """Admin-only user management page"""
    user = await _get_current_user_from_request(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+sign+in+as+admin", status_code=303)

    if user.get("role") != UserRole.ADMIN.value:
        target = quote_plus("/admin")
        return RedirectResponse(
            url=f"/access-denied?required_role=ADMIN&current_role={user.get('role', 'UNKNOWN')}&target={target}",
            status_code=303,
        )

    return templates.TemplateResponse("admin_panel.html", {"request": request, "current_user": user})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth_server",
        "port": settings.PORT,
        "version": "1.0.0"
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
