from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routes.v1 import router as v1_router
from .routes import auth as auth_routes


app = FastAPI(title="AI4Bharat FastAPI Backend", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load environment variables from .env file on application startup."""
    load_dotenv(override=True)


@app.get("/up")
async def up():
    return {"status": "ok"}


app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])


