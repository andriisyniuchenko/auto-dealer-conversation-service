from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    opensearch_url: str = "http://localhost:9200"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    crm_api_url: str
    crm_api_key: str

    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str = ""

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "galaxy-motors-chat"

    assistant_name: str = "Jessica"

    class Config:
        env_file = ".env"


settings = Settings()