import sys
import uvicorn
from app.config import settings

# Ensure UTF-8 stdout on Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("🗼 Lighthouse / Homewatch — Notion-styled DNS Shield")
    print(f"⚡ Starting server on http://{settings.host}:{settings.port}")
    print(f"📊 Mode: {'Simulation / Mock (Auto)' if not settings.force_mock_mode else 'Forced Mock'}")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
