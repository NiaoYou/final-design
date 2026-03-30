# Metabolomics Data Processing Backend (MVP)

这是基于 `SYSTEM_ARCHITECTURE.md` 生成的代谢组学数据处理系统后端 MVP 骨架（FastAPI + SQLite）。

## 已实现（MVP 主链路）
- 上传 csv/xlsx（支持“长表 long format”）
- 数据预览（返回前 20 行）
- 创建/配置任务
- 数据预处理（缺失率统计、log 变换、标准化、特征过滤）
- 缺失值填充（mean / median / knn）
- 简化版批次效应校正（mimic ComBat 的均值/方差校正）
- PCA 可视化（生成散点图并返回图表数据）

## 运行方式
1. 安装依赖：
   - `pip install -r requirements.txt`
2. 启动服务：
   - `uvicorn app.main:app --reload --port 8000`

## API
- `POST /api/upload`
- `GET  /api/datasets/{task_id}/preview`
- `POST /api/tasks`
- `GET  /api/tasks`
- `GET  /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/preprocess`
- `POST /api/tasks/{task_id}/impute`
- `POST /api/tasks/{task_id}/batch-correct`
- `GET  /api/tasks/{task_id}/evaluation`

更多请求字段请查看对应的 `schemas/` 与路由文件。

