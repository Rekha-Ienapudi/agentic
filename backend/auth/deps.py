from fastapi import Request, HTTPException
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY")

def get_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(401, "Missing token")

    token = auth.split()[1]

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(401, "Invalid token")