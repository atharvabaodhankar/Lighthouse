from typing import Dict, Any, Optional
import httpx
from app.config import settings

def format_telegram_report(summary: Dict[str, Any], top_ads: list, devices_count: int) -> str:
    """Format a clean markdown report for Telegram."""
    status_icon = "🟢 ACTIVE" if summary.get("status") == "enabled" else "🔴 PAUSED"
    today_queries = summary.get("dns_queries_today", 0)
    today_blocked = summary.get("ads_blocked_today", 0)
    percent_blocked = summary.get("ads_percentage_today", 0)
    
    top_blocked_str = ""
    for idx, item in enumerate(top_ads[:3], 1):
        top_blocked_str += f"  {idx}. `{item['domain']}` ({item['count']:,} hits)\n"

    msg = (
        f"🗼 *Lighthouse Home Shield — Daily Report*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Status:* {status_icon}\n"
        f"• *Total Queries (24h):* `{today_queries:,}`\n"
        f"• *Blocked Trackers & Ads:* `{today_blocked:,}` (*{percent_blocked}%*)\n"
        f"• *Active Devices Protected:* `{devices_count}`\n"
        f"• *Gravity Blocklist:* `{summary.get('domains_being_blocked', 0):,}` domains\n\n"
        f"🛑 *Top Blocked Threats & Trackers:*\n"
        f"{top_blocked_str}\n"
        f"⚡ *Response Latency:* ~{summary.get('avg_latency_ms', 11)} ms\n"
        f"📍 *Resolver Region:* AWS ap-south-1 (Mumbai)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 _Protected via Lighthouse Static EIP_"
    )
    return msg


async def send_telegram_alert(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    custom_message: Optional[str] = None
) -> Dict[str, Any]:
    token = bot_token or settings.telegram_bot_token
    cid = chat_id or settings.telegram_chat_id

    if not token or not cid:
        return {
            "success": False,
            "error": "Telegram Bot Token or Chat ID not configured. Set them in .env or via the UI settings."
        }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": custom_message or "🗼 Test notification from Lighthouse DNS Shield.",
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return {"success": True, "details": "Message dispatched successfully"}
            else:
                return {"success": False, "error": f"Telegram API error: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

