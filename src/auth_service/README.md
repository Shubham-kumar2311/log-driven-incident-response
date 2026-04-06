# Central Authentication Service

FastAPI-based centralized authentication and user access control system for the Log-Driven Incident Response Platform.

## Features

- **JWT-based Authentication**: Secure token generation and verification
- **Role-Based Access Control (RBAC)**: USER, ANALYST, ADMIN roles with hierarchical permissions
- **User Management**: Admin panel for user creation, role assignment, and access control
- **Login/Registration**: Web-based login and self-registration with email validation
- **Security**:
  - Password hashing with bcrypt
  - Brute-force detection and rate limiting
  - Access-denied UX with redirect flow
  - Audit logging for admin actions
- **Cross-Service Integration**: Cookie-based authentication across microservices

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB running locally or remote
- Virtual environment (recommended)

### Installation

```bash
cd src/auth_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Copy and configure the environment file:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key environment variables:
- `AUTH_HOST`: Server host (default: 0.0.0.0)
- `AUTH_PORT`: Server port (default: 3000)
- `MONGODB_URL`: MongoDB connection string
- `JWT_SECRET`: Secret key for JWT signing
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Running the Service

```bash
python app.py
```

Service will start on `http://localhost:3000`

## API Endpoints

### Authentication Routes

#### Login
```
POST /login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response: 200 OK
{
  "success": true,
  "redirect_url": "http://localhost:8001",
  "user": {
    "id": "...",
    "username": "user@example.com",
    "role": "USER"
  }
}
```

#### Register
```
POST /register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123"
}

Response: 201 Created
{
  "success": true,
  "user": { ... }
}
```

#### Verify Token
```
GET /verify
Cookie: auth_token=...

Response: 200 OK
{
  "authenticated": true,
  "user": { ... }
}
```

#### Logout
```
GET /logout

Response: 303 See Other
Location: /login
```

### Admin Endpoints

#### List Users (search required)
```
GET /admin/users?search=john&limit=25&page=1
Authorization: Admin role required

Response: 200 OK
{
  "success": true,
  "data": {
    "users": [...],
    "total": 5,
    "page": 1,
    "pages": 1
  }
}
```

#### Update User Role
```
PATCH /admin/users/{user_id}/role
Content-Type: application/json
Authorization: Admin role required

{
  "role": "ANALYST"
}

Response: 200 OK
{
  "success": true,
  "user": { ... }
}
```

## Web Interfaces

### Login Page
- **URL**: `http://localhost:3000/login`
- **Purpose**: User authentication
- **Access**: Public (no auth required)

### Register Page
- **URL**: `http://localhost:3000/register`
- **Purpose**: User self-registration (default role: USER)
- **Access**: Public (no auth required)

### Admin Panel
- **URL**: `http://localhost:3000/admin`
- **Purpose**: User management and role assignment
- **Access**: ADMIN role only
- **Features**:
  - Search users by username/email
  - Change user roles (USER → ANALYST → ADMIN)
  - View all user details
  - Real-time role updates

### Access Denied Page
- **URL**: `http://localhost:3000/access-denied`
- **Purpose**: Friendly error page for insufficient permissions
- **Features**:
  - Shows current and required role
  - Logout button with animated overlay
  - Login with different account option

## Role Hierarchy

Users are assigned one of three roles with role-based policy enforcement:

| Role | Level | Services | Notes |
|------|-------|----------|-------|
| **USER** | 1 | Log Ingestion (8001) | Default for new registrations |
| **ANALYST** | 2 | Incident Management (8004) | Can view and manage incidents |
| **ADMIN** | 3 | Response Service (8005) + Admin Panel (3000) | Full system access, user management |

Role hierarchy is enforced: ADMIN > ANALYST > USER. Higher roles inherit lower role permissions.

## Database Schema

### Users Collection

```json
{
  "_id": "ObjectId",
  "username": "string (unique, lowercase)",
  "email": "string (unique, lowercase)",
  "password_hash": "string",
  "role": "USER|ANALYST|ADMIN",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_login_at": "datetime",
  "last_login_ip": "string"
}
```

### Login Logs Collection

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "username_attempted": "string",
  "ip_address": "string",
  "status": "SUCCESS|FAILED",
  "user_agent": "string",
  "failure_reason": "string (optional)",
  "timestamp": "datetime"
}
```

## Security Considerations

1. **Secrets Management**:
   - Never commit `.env` file to repository
   - Use `.env.example` as template
   - Rotate JWT_SECRET in production

2. **Brute Force Protection**:
   - Configurable failed attempt threshold
   - Time window for attempt counting
   - IP-based and username-based tracking

3. **Password Policy**:
   - Minimum 8 characters
   - Mixed case (upper + lower)
   - Numbers and special characters required
   - Bcrypt hashing with 12 rounds

4. **Session Management**:
   - HttpOnly cookie flag prevents XSS access
   - SameSite=Lax prevents CSRF (configurable for lax mode during dev)
   - Secure flag required in HTTPS production

## Testing

### Manual Test Workflow

1. **Register new user**:
   ```bash
   curl -X POST http://localhost:3000/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "TestPass123!"
     }'
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:3000/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "TestPass123!"
     }' \
     -c cookies.txt
   ```

3. **Verify authentication**:
   ```bash
   curl http://localhost:3000/verify \
     -b cookies.txt
   ```

4. **Logout**:
   ```bash
   curl http://localhost:3000/logout \
     -b cookies.txt \
     -L
   ```

## Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running: `mongod`
- Check `MONGODB_URL` in `.env`
- Verify network connectivity to MongoDB server

### Token Verification Fails
- Check JWT_SECRET matches across all services
- Verify token has not expired (JWT_EXPIRE_MINUTES)
- Ensure cookie name matches (COOKIE_NAME)

### Admin Operations Fail
- Verify admin user has role="ADMIN"
- Check admin user is not self-modifying role
- Ensure at least one admin account exists

### CORS Errors
- Add target service origin to CORS_ORIGINS in .env
- Format: `http://localhost:XXXX`
- Restart service after changes

## Project Structure

```
auth_service/
├── __init__.py
├── app.py                       # FastAPI main application
├── config.py                    # Configuration and settings management
├── database.py                  # MongoDB connection and initialization
├── models.py                    # Data models (User, LoginLog)
├── client_auth_middleware.py    # Shared middleware for other services
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration (local)
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── auth/
│   ├── __init__.py
│   └── routes.py                # Authentication API routes
├── middleware/
│   ├── __init__.py
│   └── auth.py                  # Authentication middleware
├── utils/
│   ├── __init__.py
│   ├── jwt.py                   # JWT token utilities
│   ├── password.py              # Password hashing/validation
│   └── detection.py             # Anomaly detection integration
├── templates/
│   ├── login.html               # Login page
│   ├── register.html            # Registration page
│   ├── admin_panel.html         # Admin user management UI
│   └── access_denied.html       # Access denied page
└── static/                      # Static assets (CSS, JS)
```

## Contributing

When modifying auth service:
1. Update `.env.example` if adding new environment variables
2. Document new API endpoints in this README
3. Add tests for new authentication features
4. Follow existing code style and patterns

## License

Internal use only. Part of Log-Driven Incident Response Platform.
