from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db


def get_db_dep() -> Generator[Session, None, None]:
    # 使用 yield 让 FastAPI 在请求结束后自动触发 finally 逻辑。
    yield from get_db()

