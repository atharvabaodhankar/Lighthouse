import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Settings(BaseModel):
    app_name: str = "Lighthouse"
    app_tagline: str = "Home Network DNS Shield & Traffic Intelligence"
    
    # Pi-hole Connection
    pihole_url: str = os.getenv("PIHOLE_URL", "http://127.0.0.1:8080")
    pihole_api_token: str = os.getenv("PIHOLE_API_TOKEN", "")
    
    # Auto-fallback to mock mode if real Pi-hole is not reachable
    force_mock_mode: bool = os.getenv("MOCK_MODE", "").lower() in ("true", "1", "yes")
    
    # Telegram daily digest / notifications
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Server runtime
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")


settings = Settings()

