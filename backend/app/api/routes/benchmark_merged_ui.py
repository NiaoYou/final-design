from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import benchmark_merged_read as bmr

router = APIRouter(tags=["benchmark_merged_ui"])

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


@router.get("/benchmark/merged", response_class=HTMLResponse)
def benchmark_merged_results_page(request: Request):
    summary = bmr.build_summary_payload()
    report = bmr.load_batch_correction_method_report()
    metrics = bmr.load_batch_correction_metrics()
    files = bmr.list_downloadable_files()
    pca_url = "/api/benchmark/merged/assets/pca_before_vs_after.png"
    key_cards = bmr.build_key_metric_cards(metrics)
    interpretation = bmr.build_interpretation_from_reports(metrics, report)
    system_capabilities = bmr.system_capabilities_bullets()
    return _TEMPLATES.TemplateResponse(
        "benchmark_merged.html",
        {
            "request": request,
            "summary": summary,
            "report": report,
            "metrics": metrics,
            "files": files,
            "pca_url": pca_url,
            "key_metric_cards": key_cards,
            "interpretation": interpretation,
            "system_capabilities": system_capabilities,
        },
    )
