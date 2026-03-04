from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    linkedin_cookie: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen3:8b"
    ollama_timeout: int = 300
    ollama_api_key: str = "ollama"
    request_timeout: int = 30
    fastapi_url: str = "http://localhost:8000/api/v1/rate-job"
    telegram_bot_token: str = ""
    telegram_user_id: int = 0

    class Config:
        env_file = ".env"


settings = Settings()