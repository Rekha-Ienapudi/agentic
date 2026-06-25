from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.utils import create_token

router = APIRouter()

# Demo users — matches the frontend's mock accounts exactly
_USERS = {
    "john.doe@cgi.com": {
        "id": "u1",
        "name": "John Doe",
        "password": "demo123",
        "role": "executive",
        "roleLabel": "Supply Chain Executive Advisor",
        "initials": "JD",
    },
    "max.mustermann@cgi.com": {
        "id": "u2",
        "name": "Max Mustermann",
        "password": "demo123",
        "role": "operations",
        "roleLabel": "Supply Chain Manager",
        "initials": "MM",
    },
    "lisa.transport@cgi.com": {
        "id": "u3",
        "name": "Lisa Transport",
        "password": "demo123",
        "role": "logistics",
        "roleLabel": "Logistics & Transportation Manager",
        "initials": "LT",
    },
}


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    user = _USERS.get(req.email.lower())
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "id": user["id"],
        "name": user["name"],
        "email": req.email.lower(),
        "role": user["role"],
        "roleLabel": user["roleLabel"],
        "initials": user["initials"],
        "token": create_token({"sub": user["id"], "role": user["role"]}),
    }
