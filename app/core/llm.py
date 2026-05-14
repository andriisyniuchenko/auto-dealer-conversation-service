from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def get_llm() -> BaseChatModel:
    return init_chat_model(
        settings.llm_model,
        model_provider=settings.llm_provider,
        temperature=0.7,
    )