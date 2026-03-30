from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import Settings


DB_URL = f"sqlite:///{Settings.DB_PATH}"

# sqlite: 允许多线程访问（仅用于本地开发/课程演示）
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """
    初始化数据库：创建表结构。
    """

    # 导入模型以注册到 Base.metadata
    from app.models.dataset import Dataset  # noqa: F401
    from app.models.parameters import Parameters  # noqa: F401
    from app.models.result import Result  # noqa: F401
    from app.models.task import Task  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

