#!/usr/bin/env python3
"""
Password-based Authentication System

This module provides traditional username/password authentication
alongside the existing Microsoft OAuth system.

Features:
- User registration with email verification
- Username/password login
- Email verification
- Password hashing with bcrypt
- Login attempt monitoring
"""

import bcrypt
import secrets
import smtplib
import ssl
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
config_path = Path(__file__).parent.parent.parent / "config" / ".env"
load_dotenv(config_path)

logger = logging.getLogger(__name__)

class PasswordAuthManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_username)
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "University Advisor")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        
        # Validation patterns
        self.username_pattern = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
        self.email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        self.password_pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
    
    def _extract_value(self, cursor_result):
        """Helper function to safely extract value from cursor result (handles RealDictRow)"""
        if cursor_result is None:
            return None
        if isinstance(cursor_result, dict):
            # RealDictRow - get the first value
            return list(cursor_result.values())[0] if cursor_result else None
        elif hasattr(cursor_result, '__getitem__'):
            # Tuple or list
            return cursor_result[0] if cursor_result else None
        else:
            # Direct value
            return cursor_result
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def validate_username(self, username: str) -> bool:
        """Validate username format"""
        return bool(self.username_pattern.match(username))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        return bool(self.password_pattern.match(password))
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_verification_token(self) -> str:
        """Generate secure verification token"""
        return secrets.token_urlsafe(32)
    
    def check_username_availability(self, username: str) -> bool:
        """Check if username is available"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM users WHERE username = %s",
                        (username,)
                    )
                    count = self._extract_value(cur.fetchone())
                    return count == 0
        except Exception as e:
            logger.error(f"Error checking username availability: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    
    def check_email_availability(self, email: str) -> bool:
        """Check if email is available"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM users WHERE email = %s",
                        (email.lower(),)
                    )
                    count = self._extract_value(cur.fetchone())
                    return count == 0
        except Exception as e:
            logger.error(f"Error checking email availability: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: str, last_name: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Register a new user with email verification
        
        Returns:
            Dict with registration result and user_id if successful
        """
        # Validate inputs
        username = username.strip()
        email = email.lower().strip()
        first_name = first_name.strip()
        last_name = last_name.strip()
        
        # Validation checks
        if not self.validate_username(username):
            raise HTTPException(
                status_code=400, 
                detail="Username must be 3-30 characters and contain only letters, numbers, and underscores"
            )
        
        if not self.validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not self.validate_password(password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters with uppercase, lowercase, and number"
            )
        
        if not first_name or not last_name:
            raise HTTPException(status_code=400, detail="First name and last name are required")
        
        # Check availability
        if not self.check_username_availability(username):
            raise HTTPException(status_code=409, detail="Username already exists")
        
        if not self.check_email_availability(email):
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # Generate tokens and hash password
        verification_token = self.generate_verification_token()
        password_hash = self.hash_password(password)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Create user with verification
                    cur.execute("""
                        SELECT create_user_with_verification(%s, %s, %s, %s, %s, %s)
                    """, (username, email, password_hash, first_name, last_name, verification_token))
                    
                    user_id = self._extract_value(cur.fetchone())
                    
                    # Log verification email
                    cur.execute("""
                        INSERT INTO email_verification_logs 
                        (user_id, email, verification_token, expires_at, ip_address)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        user_id, email, verification_token, 
                        datetime.now() + timedelta(hours=24),
                        ip_address
                    ))
                    
                    conn.commit()
                    
                    # Send verification email
                    self.send_verification_email(email, verification_token, first_name)
                    
                    logger.info(f"User registered successfully: {username} ({email})")
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "message": "Registration successful. Please check your email for verification.",
                        "email": email
                    }
                    
        except psycopg2.IntegrityError as e:
            if "username" in str(e):
                raise HTTPException(status_code=409, detail="Username already exists")
            elif "email" in str(e):
                raise HTTPException(status_code=409, detail="Email already registered")
            else:
                logger.error(f"Registration integrity error: {e}")
                raise HTTPException(status_code=400, detail="Registration failed")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(status_code=500, detail="Registration failed")
    
    def authenticate_user(self, identifier: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Authenticate user with username/email and password
        
        Args:
            identifier: Username or email
            password: User password
            ip_address: Client IP for logging
        
        Returns:
            Dict with user data if successful
        """
        identifier = identifier.strip().lower()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get user by username or email
                    cur.execute("""
                        SELECT id, username, email, password_hash, email_verified, 
                               is_active, locked_until, failed_login_attempts,
                               first_name, last_name, display_name
                        FROM users 
                        WHERE (username = %s OR email = %s) 
                        AND auth_method IN ('password', 'both')
                    """, (identifier, identifier))
                    
                    user = cur.fetchone()
                    
                    # Log failed attempt if user not found
                    if not user:
                        self.log_login_attempt(
                            identifier, ip_address, False, "password", 
                            "user_not_found"
                        )
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Check if account is locked
                    if user['locked_until'] and user['locked_until'] > datetime.now():
                        self.log_login_attempt(
                            identifier, ip_address, False, "password",
                            "account_locked"
                        )
                        raise HTTPException(
                            status_code=423, 
                            detail="Account temporarily locked due to failed login attempts"
                        )
                    
                    # Check if account is active
                    if not user['is_active']:
                        self.log_login_attempt(
                            identifier, ip_address, False, "password",
                            "account_disabled"
                        )
                        raise HTTPException(status_code=401, detail="Account disabled")
                    
                    # Check if email is verified
                    if not user['email_verified']:
                        self.log_login_attempt(
                            identifier, ip_address, False, "password",
                            "email_not_verified"
                        )
                        raise HTTPException(
                            status_code=403, 
                            detail={
                                "message": "Please verify your email before logging in",
                                "email": user['email'],
                                "can_resend": True,
                                "error_type": "email_not_verified"
                            }
                        )
                    
                    # Verify password
                    if not self.verify_password(password, user['password_hash']):
                        self.log_login_attempt(
                            identifier, ip_address, False, "password",
                            "invalid_password"
                        )
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Successful login
                    self.log_login_attempt(identifier, ip_address, True, "password")
                    
                    logger.info(f"User authenticated successfully: {user['username']} ({user['email']})")
                    
                    return {
                        "id": user['id'],
                        "username": user['username'],
                        "email": user['email'],
                        "name": user['display_name'],
                        "first_name": user['first_name'],
                        "last_name": user['last_name'],
                        "auth_method": "password"
                    }
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")
    
    def verify_email(self, verification_token: str) -> bool:
        """Verify user email with verification token"""
        logger.info(f"[VERIFY_DEBUG] Starting verification for token: {verification_token[:15]}... (length: {len(verification_token)})")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # First check if user exists with this token
                    cur.execute("""
                        SELECT id, email, email_verified, email_verification_expires
                        FROM users 
                        WHERE email_verification_token = %s
                    """, (verification_token,))
                    
                    user = cur.fetchone()
                    
                    if not user:
                        logger.warning(f"[VERIFY_DEBUG] No user found with token: {verification_token[:15]}...")
                        return False
                    
                    logger.info(f"[VERIFY_DEBUG] Found user: {user['email']}, already verified: {user['email_verified']}")
                    logger.info(f"[VERIFY_DEBUG] Token expires: {user['email_verification_expires']}")
                    
                    # Use the database function
                    cur.execute("SELECT verify_user_email(%s)", (verification_token,))
                    verified = self._extract_value(cur.fetchone())
                    
                    if verified:
                        logger.info(f"Email verified successfully with token: {verification_token[:10]}...")
                    else:
                        logger.warning(f"Email verification failed with token: {verification_token[:10]}...")
                    
                    return verified
                    
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            return False
    
    def resend_verification_email(self, email: str) -> bool:
        """Resend verification email to user"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get user if email not verified and registration recent
                    cur.execute("""
                        SELECT id, first_name, email, created_at
                        FROM users 
                        WHERE email = %s 
                        AND NOT email_verified 
                        AND created_at > NOW() - INTERVAL '7 days'
                    """, (email.lower(),))
                    
                    user = cur.fetchone()
                    if not user:
                        return False
                    
                    # Generate new verification token
                    verification_token = self.generate_verification_token()
                    
                    # Update user with new token
                    cur.execute("""
                        UPDATE users 
                        SET email_verification_token = %s,
                            email_verification_expires = %s
                        WHERE id = %s
                    """, (
                        verification_token,
                        datetime.now() + timedelta(hours=24),
                        user['id']
                    ))
                    
                    # Log new verification email
                    cur.execute("""
                        INSERT INTO email_verification_logs 
                        (user_id, email, verification_token, expires_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        user['id'], email, verification_token,
                        datetime.now() + timedelta(hours=24)
                    ))
                    
                    conn.commit()
                    
                    # Send new verification email
                    self.send_verification_email(email, verification_token, user['first_name'])
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Resend verification error: {e}")
            return False
    
    def send_verification_email(self, email: str, verification_token: str, first_name: str):
        """Send email verification email"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured - skipping email send")
            return
        
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify Your Gannon University Advisor Account"
        msg["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
        msg["To"] = email
        
        # Create HTML email
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png" 
                         alt="Gannon University" style="height: 60px;">
                    <h2 style="color: #a41e22; margin-top: 15px;">Welcome to University Advisor!</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 25px;">
                    <h3 style="color: #333; margin-top: 0;">Hi {first_name},</h3>
                    <p>Thank you for registering with Gannon University Academic Advisor! 
                       To complete your registration, please verify your email address by clicking the button below.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #a41e22; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;
                                  display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        This verification link will expire in 24 hours. If you didn't create an account, 
                        you can safely ignore this email.
                    </p>
                </div>
                
                <div style="border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 14px;">
                    <p>If you're having trouble clicking the button, copy and paste this URL into your browser:</p>
                    <p style="word-break: break-all; color: #a41e22;">{verification_url}</p>
                    
                    <p style="margin-top: 30px;">
                        Best regards,<br>
                        <strong>Gannon University Academic Advisor Team</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text = f"""
        Welcome to Gannon University Academic Advisor!
        
        Hi {first_name},
        
        Thank you for registering! To complete your registration, please verify your 
        email address by visiting this link:
        
        {verification_url}
        
        This verification link will expire in 24 hours. If you didn't create an 
        account, you can safely ignore this email.
        
        Best regards,
        Gannon University Academic Advisor Team
        """
        
        # Attach parts
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        try:
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Verification email sent to: {email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            # Don't raise exception - registration should still succeed
    
    def log_login_attempt(self, identifier: str, ip_address: str, success: bool, 
                         auth_method: str, failure_reason: str = None):
        """Log login attempt for security monitoring"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT log_login_attempt(%s, %s, %s, %s, %s)
                    """, (identifier, ip_address, success, auth_method, failure_reason))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")


# Global instance
password_auth_manager = PasswordAuthManager()

def get_password_auth_manager() -> PasswordAuthManager:
    """Get the password authentication manager instance"""
    return password_auth_manager