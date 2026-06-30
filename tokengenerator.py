from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from database import add_refresh_token, validate_refresh_token
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("HASHING_ALGORITHM")
TOKEN_EXPIRY = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

def generate_tokens(data:dict):
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    return {
        "access_token" : access_token,
        "refresh_token" : refresh_token
    }

def create_access_token(data:dict):
    payload = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes = TOKEN_EXPIRY)
    
    payload.update({"exp": expire})
    
    return jwt.encode(payload,SECRET_KEY,algorithm = ALGORITHM)
    

def create_refresh_token(data:dict):
    payload = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days = 7)
    
    payload.update({"exp": expire})
    
    refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    hashed_refresh_token = password_hash.hash(refresh_token)
    return add_refresh_token(payload,hashed_refresh_token)
    

def verify_token(token:str):
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        return None
    return payload

def verify_refresh_token(token:str):
    if token is None:
        return None
    try: 
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= [ALGORITHM]
        )
    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid token verification failed ! Login again"
        )
    
    return validate_refresh_token(payload,token)