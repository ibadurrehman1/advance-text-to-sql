from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from app.core.config import settings

load_dotenv()


class LLMUtility:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMUtility, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not LLMUtility._initialized:
            self.primary_model = init_chat_model(
                model=settings.ai.PRIMARY_MODEL_NAME,
                temperature=settings.ai.PRIMARY_MODEL_TEMPERATURE,
            )
            self.secondary_model = init_chat_model(
                model=settings.ai.SECONDARY_MODEL_NAME,
                temperature=settings.ai.SECONDARY_MODEL_TEMPERATURE,
            )
            LLMUtility._initialized = True

    def get_primary_model(self):
        return self.primary_model

    def get_secondary_model(self):
        return self.secondary_model


llm_utility = LLMUtility()
