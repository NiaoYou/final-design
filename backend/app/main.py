from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes.benchmark_merged import router as benchmark_merged_router
from app.api.routes.benchmark_merged_ui import router as benchmark_merged_ui_router
from app.api.routes.dataset import router as dataset_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.upload import router as upload_router
from app.core.config import Settings
from app.core.database import init_db
from app.core.logger import setup_logging


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup：确保目录存在并初始化数据库
    for p in [Settings.UPLOAD_DIR, Settings.PROCESSED_DIR, Settings.RESULTS_DIR, Settings.TEMP_DIR]:
        os.makedirs(p, exist_ok=True)
    init_db()
    yield
    # shutdown：此处可添加清理逻辑


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Metabolomics Data Processing System",
        description="FastAPI backend MVP generated from SYSTEM_ARCHITECTURE.md",
        version="0.1.0",
        lifespan=_lifespan,
    )

    # Vue 独立前端（Vite）联调：仅放开跨域，不改动业务逻辑
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root_redirect() -> RedirectResponse:
        """答辩演示：根路径进入 merged 结果仪表盘（不重做业务逻辑）。"""
        return RedirectResponse(url="/benchmark/merged", status_code=302)

    app.include_router(upload_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(benchmark_merged_router)
    app.include_router(benchmark_merged_ui_router)
    app.include_router(dataset_router)
    return app


app = create_app()

