from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    chroma_host: str
    chroma_port: int
    ollama_base_url: str
    crm_api_url: str

    class Config:
        env_file = ".env"


settings = Settings()