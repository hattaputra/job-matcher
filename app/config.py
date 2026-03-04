from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    linkedin_cookie: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen3:8b"
    ollama_timeout: int = 300
    request_timeout: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
