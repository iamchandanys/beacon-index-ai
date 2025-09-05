from src.core.app_settings import get_settings
from src.utils.get_configs import GetConfigs
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.configs = GetConfigs().get_configs()
        
    def getAzOpenAIllm(self) -> AzureChatOpenAI:
        azOpenAIllm = AzureChatOpenAI(
            api_key=self.settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=self.configs['chat_llm']['az_open_ai']['azure_deployment'],
            api_version=self.configs['chat_llm']['az_open_ai']['api_version'],
            temperature=self.configs['chat_llm']['az_open_ai']['temperature'],
            max_tokens=self.configs['chat_llm']['az_open_ai']['max_tokens'],
            max_retries=self.configs['chat_llm']['az_open_ai']['max_retries'],
            top_p=self.configs['chat_llm']['az_open_ai']['top_p'],
            streaming=True,
        )
        return azOpenAIllm
    
    def getAzOpenAIEmbeddings(self) -> AzureOpenAIEmbeddings:
        azOpenAIEmbeddings = AzureOpenAIEmbeddings(
            api_key=self.settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
            model=self.configs['chat_llm']['az_open_ai_embeddings']['azure_deployment'],
            openai_api_version=self.configs['chat_llm']['az_open_ai_embeddings']['api_version'],
        )
        return azOpenAIEmbeddings