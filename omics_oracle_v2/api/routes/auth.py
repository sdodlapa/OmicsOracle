"""
Authentication API routes.

This module provides endpoints for user authentication including
registration, login, password management, and token operations.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from omics_oracle_v2.auth import crud
from omics_oracle_v2.auth.dependencies import get_current_active_user
from omics_oracle_v2.auth.models import User
from omics_oracle_v2.auth.schemas import (
    LoginRequest,
    PasswordChange,
    PasswordReset,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserResponse,
)
from omics_oracle_v2.auth.security import (
    create_access_token,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
)
from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user account.

    Creates a new user with the provided email and password.
    Email must be unique and password must meet strength requirements.

    Args:
        user: User registration data
        db: Database session

    Returns:
        Created user (without password)

    Raises:
        HTTPException 400: If email is already registered
    """
    # Check if user already exists
    existing_user = await crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    db_user = await crud.create_user(db, user=user)

    # TODO: Send verification email
    # verification_token = create_email_verification_token(user.email)
    # await send_verification_email(user.email, verification_token)

    return db_user


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Login with email and password.

    Authenticates a user and returns a JWT access token.

    Args:
        credentials: Login credentials (email and password)
        db: Database session

    Returns:
        JWT access token and metadata

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Get user by email
    user = await crud.get_user_by_email(db, email=credentials.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    await crud.update_user_last_login(db, user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,  # Convert to seconds
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Refresh access token.

    Generate a new JWT token for the current user.
    Requires a valid existing token.

    Args:
        current_user: Current authenticated user

    Returns:
        New JWT access token
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Logout current user.

    Note: Since we're using stateless JWT tokens, logout is handled
    client-side by deleting the token. This endpoint exists for
    completeness and could be extended to maintain a token blacklist.

    Args:
        current_user: Current authenticated user
    """
    # TODO: Add token to blacklist (requires Redis/database)
    # For now, logout is client-side only
    pass


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user information.

    Returns the profile of the currently authenticated user.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile
    """
    return current_user


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Change user password.

    Requires the current password for verification.

    Args:
        password_data: Old and new passwords
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 400: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update password
    await crud.update_user_password(db, current_user, password_data.new_password)


@router.post("/password/reset-request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request password reset.

    Sends a password reset email to the user if the email exists.
    Always returns success to prevent email enumeration.

    Args:
        request: Password reset request with email
        db: Database session

    Returns:
        Success message
    """
    # Get user (don't reveal if email exists)
    user = await crud.get_user_by_email(db, email=request.email)

    if user:
        # TODO: Create reset token and send email
        # reset_token = create_password_reset_token(user.email)
        # await send_password_reset_email(user.email, reset_token)
        pass

    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent",
    }


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Reset password using reset token.

    Args:
        reset_data: Reset token and new password
        db: Database session

    Raises:
        HTTPException 400: If token is invalid or expired
    """
    # Verify reset token
    email = verify_password_reset_token(reset_data.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = await crud.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update password
    await crud.update_user_password(db, user, reset_data.new_password)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Verify user email address.

    Args:
        token: Email verification token
        db: Database session

    Raises:
        HTTPException 400: If token is invalid or expired
    """
    # Verify token
    email = verify_email_verification_token(token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Get user
    user = await crud.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Verify email
    await crud.verify_user_email(db, user)
