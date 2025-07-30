from src.services.large_language_models.llm_service import LLMService

if __name__ == "__main__":
    llm_service = LLMService()
    az_llm = llm_service.getAzOpenAIllm()
    response = az_llm.invoke("Hello, how are you?")  # Example usage
    print(response)  # Print the response from the LLM