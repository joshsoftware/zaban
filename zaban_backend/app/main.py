from fastapi import FastAPI
from .routes.v1 import router as v1_router


app = FastAPI(title="AI4Bharat FastAPI Backend", version="0.1.0")


@app.get("/up")
async def up():
    return {"status": "ok"}


app.include_router(v1_router, prefix="/api/v1")


