from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("HASHING_ALGORITHM")
TOKEN_EXPIRY = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def create_access_token(data:dict):
    payload = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes = TOKEN_EXPIRY)
    
    payload.update({"exp": expire})
    
    return jwt.encode(payload,SECRET_KEY,algorithm = ALGORITHM)

def verify_token(token:str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    return payload