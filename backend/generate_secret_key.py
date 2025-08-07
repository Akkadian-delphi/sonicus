#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for production deployment
"""

import secrets
import string

def generate_secret_key(length=64):
    """Generate a cryptographically secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for i in range(length))

if __name__ == "__main__":
    print("Generated SECRET_KEY for production:")
    print(generate_secret_key())
    print("\nUse this value for the SECRET_KEY environment variable in Coolify")
