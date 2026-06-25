from jose import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("SECRET_KEY")

def create_token(data):
    return jwt.encode(
        {**data, "exp": datetime.utcnow() + timedelta(hours=8)},
        SECRET_KEY,
        algorithm="HS256",
    )