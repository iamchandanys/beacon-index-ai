import os

from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import AzureOpenAIModel
from deepeval import evaluate
from src.utils.get_configs import GetConfigs
from src.core.app_settings import get_settings

# Metrics:
# Answer Relevancy: Is the answer actually about what the user asked? (Checks if the response matches the user's question topic)
# Faithfulness: Is the answer fully supported by the retrieved context  (no hallucinations)? (Checks if the answer is factually correct, with no contradictions)
# Contextual Relevancy: How much of the retrieved context is actually related to the question? (Looks for relevant info in the context, not random info)
# Contextual Precision: Are the most relevant info chunks placed at the top of the retrieved documents? (Checks ranking of best info in retrieval)
# Contextual Recall: Did your retrieval include all info needed to answer the question? (Checks for missing important context in what was retrieved)

class DeepevalEvaluate:
    def __init__(self):
        self.configs = GetConfigs().get_configs()
        self.app_settings = get_settings()

        # Set the Confident API key if not already set
        if not os.environ.get("CONFIDENT_API_KEY"):
            os.environ["CONFIDENT_API_KEY"] = self.app_settings.DEEPEVAL_API_KEY

        # To disable opening the DeepEval dashboard whenever a request is made
        os.environ["DEEPEVAL_DASHBOARD_DISABLED"] = "1"

    def __get_model(self) -> AzureOpenAIModel:
        model = AzureOpenAIModel(
            model_name=self.configs['deepeval']['model_name'],
            deployment_name=self.configs['deepeval']['deployment_name'],
            azure_openai_api_key=self.app_settings.AZURE_OPENAI_API_KEY,
            openai_api_version=self.configs['deepeval']['openai_api_version'],
            azure_endpoint=self.configs['deepeval']['azure_endpoint'],
            temperature=self.configs['deepeval']['temperature']
        )
        return model
    
    def evaluate(self, input: str, actual_output: str, expected_output: str = None, retrieval_context: str = None):
        test_case = LLMTestCase(
            input=input,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=retrieval_context
        )

        # threshold=0.6 means that the metric will only consider a result as “passing” if its score is 0.6 or higher.
        answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.6, model=self.__get_model())
        faithfulness_metric = FaithfulnessMetric(threshold=0.6, model=self.__get_model())

        evaluate([test_case], metrics=[answer_relevancy_metric, faithfulness_metric])
