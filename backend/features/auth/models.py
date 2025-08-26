#!/usr/bin/env python3
"""
Pydantic models for password-based authentication
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
import re

class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError('Password must be at least 8 characters with uppercase, lowercase, and number')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip().title()

class UserLoginRequest(BaseModel):
    identifier: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class UserRegistrationResponse(BaseModel):
    success: bool
    message: str
    email: str
    user_id: Optional[str] = None

class UserLoginResponse(BaseModel):
    success: bool
    user: dict
    token: str
    message: str

class EmailVerificationRequest(BaseModel):
    token: str = Field(..., description="Email verification token")

class EmailVerificationResponse(BaseModel):
    success: bool
    message: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to resend verification to")

class ResendVerificationResponse(BaseModel):
    success: bool
    message: str

class CheckAvailabilityRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class CheckAvailabilityResponse(BaseModel):
    username_available: Optional[bool] = None
    email_available: Optional[bool] = None