from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analysis.router import router as analysis_router
from app.config import settings
from app.jquants_client import get_cache_stats
from app.stocks.router import router as stocks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("stocks-study backend started")
    yield


app = FastAPI(title="stocks-study API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    """ヘルスチェック。APIキー設定状況とキャッシュ状態を含む。"""
    api_key_configured = bool(settings.quants_api_v2_api_key)
    cache_stats = get_cache_stats()
    return {
        "status": "ok",
        "api_key_configured": api_key_configured,
        "cache": cache_stats,
    }
