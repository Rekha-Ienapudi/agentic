from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.agent import router as agent_router
from routes.auth import router as auth_router
from init_db import init_db
import os

app = FastAPI()

cors_origins = os.getenv("CORS_ORIGINS", "*")
allow_origins = [o.strip() for o in cors_origins.split(",")] if cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(agent_router, prefix="/api/agent")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Supply Chain AI Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}
