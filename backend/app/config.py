import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    recruitu_base_url: str | None = os.getenv("RECRUITU_BASE_URL")
    allowed_origins: str | None = os.getenv("ALLOWED_ORIGINS", "*")
    openai_model_extract: str = os.getenv("OPENAI_MODEL_EXTRACT", "gpt-4o-mini")
    openai_model_score: str = os.getenv("OPENAI_MODEL_SCORE", "gpt-4o-mini")

settings = Settings()
