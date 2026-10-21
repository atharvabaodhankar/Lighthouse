import os
from pathlib import Path
from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.pihole_client import pihole
from app.telegram import format_telegram_report, send_telegram_alert

app = FastAPI(
    title=settings.app_name,
    description=settings.app_tagline,
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the Notion-styled Lighthouse Single-Page App."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "app_tagline": settings.app_tagline,
            "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id)
        }
    )


@app.get("/api/summary")
async def get_summary():
    data = await pihole.get_summary()
    return JSONResponse(content=data)


@app.get("/api/chart")
async def get_chart():
    data = await pihole.get_chart_data()
    return JSONResponse(content=data)


@app.get("/api/top-items")
async def get_top_items():
    data = await pihole.get_top_items()
    return JSONResponse(content=data)


@app.get("/api/clients")
async def get_clients():
    clients = await pihole.get_clients()
    return JSONResponse(content={"clients": clients})


@app.get("/api/queries")
async def get_queries(
    limit: int = Query(50, ge=1, le=200),
    filter_type: str = Query("all", pattern="^(all|blocked|permitted)$"),
    search: str = Query("", max_length=100)
):
    queries = await pihole.get_recent_queries(limit=limit, filter_type=filter_type, search=search)
    return JSONResponse(content={"queries": queries})


@app.get("/api/rules")
async def get_rules():
    rules = await pihole.get_all_rules()
    return JSONResponse(content=rules)


@app.post("/api/rules")
async def add_rule(payload: dict = Body(...)):
    domain = payload.get("domain", "").strip()
    list_type = payload.get("list_type", "blocked")
    rule_type = payload.get("rule_type", "exact")
    comment = payload.get("comment", "")
    
    if not domain:
        return JSONResponse(status_code=400, content={"error": "Domain is required"})
        
    res = await pihole.add_rule(domain, list_type, rule_type, comment)
    return JSONResponse(content=res)


@app.delete("/api/rules")
async def delete_rule(payload: dict = Body(...)):
    domain = payload.get("domain", "")
    list_type = payload.get("list_type", "blocked")
    res = await pihole.remove_rule(domain, list_type)
    return JSONResponse(content=res)


@app.post("/api/toggle")
async def toggle_protection(payload: dict = Body(...)):
    enable = payload.get("enable", True)
    duration = payload.get("duration", 0) # seconds (0 = forever)
    res = await pihole.toggle_protection(enable, duration)
    return JSONResponse(content=res)


@app.post("/api/telegram/test")
async def trigger_telegram_test(payload: dict = Body(...)):
    bot_token = payload.get("bot_token") or settings.telegram_bot_token
    chat_id = payload.get("chat_id") or settings.telegram_chat_id
    preview_only = payload.get("preview_only", False)
    
    summary = await pihole.get_summary()
    top = await pihole.get_top_items()
    clients = await pihole.get_clients()
    
    msg = format_telegram_report(summary, top.get("top_ads", []), len(clients))
    
    if preview_only:
        return JSONResponse(content={"success": True, "preview": msg})
        
    res = await send_telegram_alert(bot_token, chat_id, msg)
    res["preview"] = msg
    return JSONResponse(content=res)


@app.post("/api/logs/flush")
async def flush_logs():
    """Flush DNS query logs on Pi-hole v6 engine."""
    res = await pihole.flush_logs()
    return JSONResponse(content=res)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
