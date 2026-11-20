from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_pool
from app.routers import auth, films, seances

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_pool()


app = FastAPI(
    lifespan=lifespan,
    title="Le Grand Cinéma - API",
    description="API de réservation de places pour le cinéma Le Grand Cinéma.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(films.router)
app.include_router(seances.router)


@app.get("/health", tags=["Technique"])
def health() -> dict[str, str]:
    return {"status": "ok"}
