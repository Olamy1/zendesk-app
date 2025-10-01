# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Routers
from backend.routers import tickets, users   # 👈 only this is correct

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Zendesk Reporting App",
    description="Internal DOE tool to manage bi-weekly Zendesk reporting",
    version="1.0.0",
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "").split(",")
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# Root health check
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Zendesk Reporting API is running"}
