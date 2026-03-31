"""
core/config.py

Application settings loaded from environment variables.
Copy .env.example to .env and fill in values.
"""

from pydantic_settings import BaseSettings
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    openai_model_primary: str = "gpt-4o"
    openai_model_fast: str = "gpt-4o-mini"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # App
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    secret_key: str = "changeme-in-production"

    # Data paths
    flows_file: Path = DATA_DIR / "flows.json"
    flow_templates_file: Path = DATA_DIR / "flow_templates.json"
    unmapped_flows_file: Path = DATA_DIR / "unmapped_flows.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
