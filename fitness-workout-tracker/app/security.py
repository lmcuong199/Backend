# os: read environment variables (settings that live outside your code)
import os
# datetime: a moment
# timedelta: duration ("60 min")
# timezone: tells Python which clock you mean 
from datetime import datetime, timedelta, timezone

# bcrypt: password hashing library. Installed separately with pip
import bcrypt
# jwt: the PyJWT library, for creating and reading login tokens 
import jwt
# load_dotenv: reads a file called .env and loads its contents as environment variables
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
# this guard makes a misconfiguration fail loudly at import time instead of producing broken tokens at runtime
# fail fast, fail obvious
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing. Add it to your .env file.")

# HS256: the signing algorithm. It means "sign this using SHA-256 with one shared secret key"
# the same key both signs and verifies, which is fine when one app does both
JWT_ALGORITHM = "HS256"
# 60: tokens die after an hour. Shorter means a stolen token is less useful; longer means fewer re-logins
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# bcrypt 5.x raises ValueError on anything longer, so we cut it ourselves
BCRYPT_MAX_BYTES = 72

# takes a string and returns a string
def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    # bcrypt.gensalt() generates a fresh random salt for every password
    # this is why 2 users with the identical password get completely different hashes
    # and why an attacker can't precompute a table of common-password hashes
    # the salt is stored inside the hash string itself, which is how checkpw knows what to use later
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

# this func re-hashes the attempt with the stored salt and compares 
# if your database leaks, the passwords aren't in it
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        # sub = subject, who this token is about
        "sub": str(user_id),  
        # iat = issued at
        "iat": now,         
        # exp = expires                              
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    # string with format: header.payload.signature
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    # Return the user id, or None if the token is invalid/expired/tampered with.
    try:
        # algorithms=[JWT_ALGORITHM] in decode is a security control, not boilerplate
        # without it, an attacker could hand you a token claiming "alg": "none" and PyJWT would accept it unsigned
        # Always pin the algorithm on the decode side
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    # jwt.InvalidTokenError is the parent class of every PyJWT failure - expired, bad signature, malformed, bad subject
    except (jwt.InvalidTokenError, KeyError, ValueError):
        # return None rather than leaking which check failed, avoid handing attackers info for free
        return None
