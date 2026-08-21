from fastapi import FastAPI

from app.api import auth_router

app = FastAPI(
    title="Veyra Finance",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Veyra Finance",
        "version": "1.0.0",
    }


app.include_router(auth_router)
