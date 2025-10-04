# Authentication System Documentation

## Overview

OmicsOracle v2.1.0 introduces a comprehensive authentication system with user management, API key support, and role-based access control (RBAC).

## Table of Contents

1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Database Setup](#database-setup)
4. [API Endpoints](#api-endpoints)
5. [Authentication Methods](#authentication-methods)
6. [User Tiers](#user-tiers)
7. [Development Guide](#development-guide)
8. [Production Deployment](#production-deployment)

---

## Features

✅ **User Management**
- Email/password authentication
- JWT token-based sessions
- Password reset functionality
- Email verification
- User profile management

✅ **API Key System**
- Generate multiple API keys per user
- Secure key storage (hashed)
- Key prefix for identification
- Revocation support
- Usage tracking

✅ **Role-Based Access Control (RBAC)**
- User roles: Regular User, Admin
- User tiers: Free, Pro, Enterprise
- Per-tier rate limiting (coming in Task 2)
- Admin-only endpoints

✅ **Security Features**
- Bcrypt password hashing
- JWT tokens with expiration
- API key cryptographic security
- Rate limiting (coming in Task 2)
- HTTPS support (production)

---

## Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -e ".[dev]"

# Verify installation
python -m alembic --version
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update:

```bash
# Critical: Generate a secure secret key
openssl rand -hex 32

# Add to .env
OMICS_AUTH_SECRET_KEY=your-generated-secret-key-here
OMICS_DB_URL=postgresql+asyncpg://omics:password@localhost:5432/omics_oracle
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb omics_oracle

# Run migrations
python -m alembic upgrade head
```

### 4. Start the Server

```bash
uvicorn omics_oracle_v2.api.main:app --reload
```

### 5. Test Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# Login to get JWT token
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Use the token in subsequent requests
curl -X GET http://localhost:8000/api/v2/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

---

## Database Setup

### Initial Migration

The authentication system requires PostgreSQL with the following tables:

**`users` table:**
- `id`: Primary key
- `email`: Unique, indexed
- `hashed_password`: Bcrypt hash
- `full_name`: Optional user name
- `tier`: User tier (free/pro/enterprise)
- `is_active`: Account status
- `is_admin`: Admin flag
- `is_verified`: Email verification status
- `request_count`: Total API requests
- `last_request_at`: Last API call timestamp
- `last_login_at`: Last login timestamp
- `created_at`: Account creation
- `updated_at`: Last profile update

**`api_keys` table:**
- `id`: Primary key
- `user_id`: Foreign key to users
- `key_prefix`: First 8 characters (for identification)
- `key_hash`: SHA-256 hash of full key
- `name`: Optional key description
- `last_used_at`: Last usage timestamp
- `request_count`: Total requests with this key
- `created_at`: Key creation
- `revoked_at`: Revocation timestamp (null if active)

### Running Migrations

```bash
# Check current migration status
python -m alembic current

# View migration history
python -m alembic history --verbose

# Upgrade to latest version
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# Rollback to specific version
python -m alembic downgrade 001
```

### Creating New Migrations

```bash
# After modifying models, create a migration
python -m alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in versions/
# Edit if needed, then apply
python -m alembic upgrade head
```

---

## API Endpoints

### Authentication Endpoints (`/api/v2/auth`)

#### `POST /auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "tier": "free",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### `POST /auth/login`
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### `POST /auth/refresh`
Refresh an existing JWT token.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### `GET /auth/me`
Get current user information.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "tier": "free",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### `POST /auth/password/change`
Change user password.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

### User Management Endpoints (`/api/v2/users`)

#### `GET /users/me/profile`
Get detailed user profile with usage statistics.

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "tier": "free"
  },
  "usage_stats": {
    "request_count": 150,
    "last_request_at": "2025-01-15T12:30:00Z"
  },
  "quota_info": {
    "tier": "free",
    "requests_used": 150,
    "requests_limit": 100,
    "requests_remaining": -50,
    "quota_exceeded": true
  }
}
```

#### `POST /users/me/api-keys`
Create a new API key.

**Request:**
```json
{
  "name": "Production API Key"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Production API Key",
  "key_prefix": "omics_12",
  "api_key": "omics_1234567890abcdef...",
  "created_at": "2025-01-15T10:00:00Z",
  "message": "Save this API key securely. It will not be shown again."
}
```

⚠️ **Important:** The full API key is only shown once during creation. Store it securely!

#### `GET /users/me/api-keys`
List all API keys for current user.

**Response:**
```json
{
  "api_keys": [
    {
      "id": 1,
      "name": "Production API Key",
      "key_prefix": "omics_12",
      "last_used_at": "2025-01-15T12:00:00Z",
      "request_count": 50,
      "created_at": "2025-01-15T10:00:00Z",
      "is_active": true
    }
  ],
  "total": 1
}
```

#### `DELETE /users/me/api-keys/{id}`
Revoke an API key.

**Response:**
```json
{
  "message": "API key revoked successfully"
}
```

### Admin Endpoints (`/api/v2/users/admin`)

Require admin privileges.

#### `PUT /users/admin/quota`
Update user tier (admin only).

**Request:**
```json
{
  "user_id": 5,
  "tier": "pro"
}
```

#### `POST /users/admin/deactivate/{user_id}`
Deactivate a user account (admin only).

#### `POST /users/admin/activate/{user_id}`
Reactivate a user account (admin only).

---

## Authentication Methods

### 1. JWT Token Authentication

Use for web applications and mobile apps.

**Flow:**
1. User logs in with email/password
2. Server returns JWT token
3. Client includes token in `Authorization` header
4. Token expires after 24 hours (configurable)
5. Refresh token to extend session

**Example:**
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v2/auth/me
```

### 2. API Key Authentication

Use for server-to-server communication, scripts, and long-running integrations.

**Flow:**
1. User creates API key via web interface or API
2. Server returns key (shown only once)
3. Client includes key in `X-API-Key` header
4. Key never expires unless revoked

**Example:**
```bash
# Create API key
curl -X POST http://localhost:8000/api/v2/users/me/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Script Key"}'

# Use API key
curl -H "X-API-Key: omics_1234567890abcdef..." \
  http://localhost:8000/api/v1/agents
```

### 3. Optional Authentication

Some endpoints support optional authentication. If authenticated, receive higher rate limits and personalized features.

---

## User Tiers

### Free Tier
- **Rate Limit:** 100 requests/hour (coming in Task 2)
- **Features:** Basic API access
- **Cost:** Free

### Pro Tier
- **Rate Limit:** 1,000 requests/hour
- **Features:**
  - Priority support
  - Advanced analytics
  - Bulk operations
- **Cost:** $29/month (planned)

### Enterprise Tier
- **Rate Limit:** Custom
- **Features:**
  - Dedicated support
  - SLA guarantees
  - Custom integrations
  - On-premise deployment
- **Cost:** Custom pricing

---

## Development Guide

### Project Structure

```
omics_oracle_v2/
├── auth/
│   ├── __init__.py          # Public API exports
│   ├── models.py            # SQLAlchemy models (User, APIKey)
│   ├── schemas.py           # Pydantic schemas (validation)
│   ├── security.py          # Password hashing, JWT, API keys
│   ├── crud.py              # Database operations
│   └── dependencies.py      # FastAPI dependencies
├── database/
│   ├── __init__.py          # Database exports
│   ├── base.py              # SQLAlchemy Base class
│   ├── session.py           # Async session management
│   └── migrations/          # Alembic migrations
│       ├── env.py           # Migration environment
│       └── versions/        # Migration files
│           └── 001_initial_user_apikey_tables.py
└── api/
    ├── routes/
    │   ├── auth.py          # Authentication endpoints
    │   └── users.py         # User management endpoints
    └── main.py              # FastAPI app with auth integration
```

### Adding Protected Endpoints

```python
from fastapi import APIRouter, Depends
from omics_oracle_v2.auth import get_current_active_user, get_current_admin_user
from omics_oracle_v2.auth.schemas import UserResponse

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Requires authentication - any active user."""
    return {"message": f"Hello {current_user.email}!"}

@router.post("/admin-only")
async def admin_endpoint(
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Requires admin privileges."""
    return {"message": "Admin access granted"}
```

### Testing

```python
# tests/api/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v2/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user):
    response = await client.post("/api/v2/auth/login", json={
        "email": test_user["email"],
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

---

## Production Deployment

### Environment Variables

**Required:**
```bash
# Security (CRITICAL - generate with: openssl rand -hex 32)
OMICS_AUTH_SECRET_KEY=your-secret-key-here

# Database
OMICS_DB_URL=postgresql+asyncpg://user:pass@host:5432/db

# NCBI (for GEO data)
NCBI_EMAIL=your.email@example.com

# OpenAI (for AI agents)
OPENAI_API_KEY=sk-your-key-here
```

**Optional:**
```bash
# Token expiration (in minutes)
OMICS_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Password reset (in hours)
OMICS_AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1

# Database pool settings
OMICS_DB_POOL_SIZE=20
OMICS_DB_MAX_OVERFLOW=40

# CORS origins
OMICS_API_CORS_ORIGINS=https://yourdomain.com
```

### Database Migration

```bash
# Production migration checklist:
1. Backup database: pg_dump omics_oracle > backup.sql
2. Test migration on staging
3. Run migration: python -m alembic upgrade head
4. Verify tables: psql -d omics_oracle -c "\dt"
5. Create first admin user
```

### Creating Admin User

```python
# scripts/create_admin.py
import asyncio
from omics_oracle_v2.auth import crud
from omics_oracle_v2.auth.schemas import UserCreate
from omics_oracle_v2.database import async_session

async def create_admin():
    async with async_session() as session:
        user_data = UserCreate(
            email="admin@example.com",
            password="SecureAdminPass123!",
            full_name="Admin User"
        )
        user = await crud.create_user(session, user_data)
        user.is_admin = True
        user.is_verified = True
        await session.commit()
        print(f"Admin user created: {user.email}")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

### Security Checklist

- [ ] Generate unique `OMICS_AUTH_SECRET_KEY` (never reuse!)
- [ ] Use PostgreSQL with SSL enabled
- [ ] Enable HTTPS in production (nginx reverse proxy)
- [ ] Set `OMICS_ENVIRONMENT=production`
- [ ] Configure CORS to only allow your domains
- [ ] Enable rate limiting (Task 2)
- [ ] Set up monitoring (Task 5)
- [ ] Regular database backups
- [ ] Rotate API keys periodically
- [ ] Monitor for suspicious activity

### Performance Optimization

```python
# omics_oracle_v2/core/config.py
class DatabaseSettings(BaseSettings):
    # Production settings
    pool_size: int = 20        # Concurrent connections
    max_overflow: int = 40     # Burst capacity
    pool_pre_ping: bool = True # Connection health check
    echo: bool = False         # Disable SQL logging
```

---

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'asyncpg'"**

```bash
pip install asyncpg
```

**2. "OSError: Multiple exceptions: Connect call failed"**

PostgreSQL is not running. Start it:
```bash
# macOS
brew services start postgresql@16

# Linux
sudo systemctl start postgresql

# Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=omics \
  -e POSTGRES_PASSWORD=omics \
  -e POSTGRES_DB=omics_oracle \
  postgres:16
```

**3. "sqlalchemy.exc.OperationalError: FATAL:  database does not exist"**

Create the database:
```bash
createdb omics_oracle
# or
docker exec -it postgres_container psql -U omics -c "CREATE DATABASE omics_oracle;"
```

**4. "Invalid token" or "401 Unauthorized"**

- Check token expiration (default: 24 hours)
- Verify `OMICS_AUTH_SECRET_KEY` matches between sessions
- Ensure `Authorization: Bearer TOKEN` header format

**5. Alembic not found or wrong version**

```bash
# Install in venv, not globally
pip install "alembic>=1.12.0"

# Use python -m to ensure venv is used
python -m alembic upgrade head
```

---

## Next Steps

- ✅ **Task 1 Complete:** Authentication system implemented
- ⏳ **Task 2 Next:** Rate limiting and quotas (Redis-based)
- 📋 **Task 3:** Persistent storage enhancements
- 📋 **Task 4:** Advanced caching (Redis)
- 📋 **Task 5:** Monitoring and metrics (Prometheus/Grafana)

See [Phase 4 Plan](../planning/PHASE_4_PRODUCTION_PLAN.md) for full roadmap.

---

## Support

For issues, questions, or feature requests:
- 📧 Email: support@omicsoracle.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: `/docs` directory
- 💬 Discussions: GitHub Discussions
