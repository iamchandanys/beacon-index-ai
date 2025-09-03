import enum
import json
import requests
from typing import Union

class MediaType(enum.Enum):
    Text = 1
    Image = 2

class Category(enum.Enum):
    Hate = 1
    SelfHarm = 2
    Sexual = 3
    Violence = 4

class Action(enum.Enum):
    Accept = 1
    Reject = 2

class _DetectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        """
        Exception raised when there is an error in detecting the content.

        Args:
        - code (str): The error code.
        - message (str): The error message.
        """
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"_DetectionError(code={self.code}, message={self.message})"


class _Decision(object):
    def __init__(
        self, suggested_action: Action, action_by_category: dict[Category, Action]
    ) -> None:
        """
        Represents the decision made by the content moderation system.

        Args:
        - suggested_action (Action): The suggested action to take.
        - action_by_category (dict[Category, Action]): The action to take for each category.
        """
        self.suggested_action = suggested_action
        self.action_by_category = action_by_category


class ContentSafety(object):
    def __init__(self, endpoint: str, subscription_key: str, api_version: str) -> None:
        """
        Creates a new ContentSafety instance.

        Args:
        - endpoint (str): The endpoint URL for the Content Safety API.
        - subscription_key (str): The subscription key for the Content Safety API.
        - api_version (str): The version of the Content Safety API to use.
        """
        self.endpoint = endpoint
        self.subscription_key = subscription_key
        self.api_version = api_version

    def build_url(self, media_type: MediaType) -> str:
        """
        Builds the URL for the Content Safety API based on the media type.

        Args:
        - media_type (MediaType): The type of media to analyze.

        Returns:
        - str: The URL for the Content Safety API.
        """
        if media_type == MediaType.Text:
            return f"{self.endpoint}/contentsafety/text:analyze?api-version={self.api_version}"
        elif media_type == MediaType.Image:
            return f"{self.endpoint}/contentsafety/image:analyze?api-version={self.api_version}"
        else:
            raise ValueError(f"Invalid Media Type {media_type}")

    def build_headers(self) -> dict[str, str]:
        """
        Builds the headers for the Content Safety API request.

        Returns:
        - dict[str, str]: The headers for the Content Safety API request.
        """
        return {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

    def build_request_body(
        self,
        media_type: MediaType,
        content: str,
        blocklists: list[str],
    ) -> dict:
        """
        Builds the request body for the Content Safety API request.

        Args:
        - media_type (MediaType): The type of media to analyze.
        - content (str): The content to analyze.
        - blocklists (list[str]): The blocklists to use for text analysis.

        Returns:
        - dict: The request body for the Content Safety API request.
        """
        if media_type == MediaType.Text:
            return {
                "text": content,
                "blocklistNames": blocklists,
            }
        elif media_type == MediaType.Image:
            return {"image": {"content": content}}
        else:
            raise ValueError(f"Invalid Media Type {media_type}")

    def detect(
        self,
        media_type: MediaType,
        content: str,
        blocklists: list[str] = [],
    ) -> dict:
        """
        Detects unsafe content using the Content Safety API.

        Args:
        - media_type (MediaType): The type of media to analyze.
        - content (str): The content to analyze.
        - blocklists (list[str]): The blocklists to use for text analysis.

        Returns:
        - dict: The response from the Content Safety API.
        """
        url = self.build_url(media_type)
        headers = self.build_headers()
        request_body = self.build_request_body(media_type, content, blocklists)
        payload = json.dumps(request_body)

        response = requests.post(url, headers=headers, data=payload)

        res_content = response.json()

        if response.status_code != 200:
            raise _DetectionError(
                res_content["error"]["code"], res_content["error"]["message"]
            )

        return res_content

    def get_detect_result_by_category(
        self, category: Category, detect_result: dict
    ) -> Union[int, None]:
        """
        Gets the detection result for the given category from the Content Safety API response.

        Args:
        - category (Category): The category to get the detection result for.
        - detect_result (dict): The Content Safety API response.

        Returns:
        - Union[int, None]: The detection result for the given category, or None if it is not found.
        """
        category_res = detect_result.get("categoriesAnalysis", None)
        
        for res in category_res:
            if category.name == res.get("category", None):
                return res
            
        raise ValueError(f"Invalid Category {category}")

    def make_decision(
        self,
        detection_result: dict,
        reject_thresholds: dict[Category, int],
    ) -> _Decision:
        """
        Makes a decision based on the Content Safety API response and the specified reject thresholds.
        Users can customize their decision-making method.

        Args:
        - detection_result (dict): The Content Safety API response.
        - reject_thresholds (dict[Category, int]): The reject thresholds for each category.

        Returns:
        - Decision: The decision based on the Content Safety API response and the specified reject thresholds.
        """
        action_result = {}
        final_action = Action.Accept
        for category, threshold in reject_thresholds.items():
            if threshold not in (-1, 0, 2, 4, 6):
                raise ValueError("RejectThreshold can only be in (-1, 0, 2, 4, 6)")

            cate_detect_res = self.get_detect_result_by_category(
                category, detection_result
            )
            if cate_detect_res is None or "severity" not in cate_detect_res:
                raise ValueError(f"Can not find detection result for {category}")

            severity = cate_detect_res["severity"]
            action = (
                Action.Reject
                if threshold != -1 and severity >= threshold
                else Action.Accept
            )
            action_result[category] = action
            if action.value > final_action.value:
                final_action = action

        if (
            "blocklistsMatch" in detection_result
            and detection_result["blocklistsMatch"]
            and len(detection_result["blocklistsMatch"]) > 0
        ):
            final_action = Action.Reject

        return _Decision(final_action, action_result)

def is_content_safe(content: str, az_cs_endpoint: str, az_cs_key: str) -> bool:
    """
    Checks if the given content is safe based on the Content Safety API.

    Args:
    - content (str): The content to be checked.

    Returns:
    - bool: True if the content is safe, False otherwise.
    """
    # Replace the placeholders with your own values
    endpoint = az_cs_endpoint
    subscription_key = az_cs_key
    api_version = "2024-09-01"

    # Initialize the ContentSafety object
    content_safety = ContentSafety(endpoint, subscription_key, api_version)

    # Set the media type and blocklists
    media_type = MediaType.Text
    blocklists = []

    # Detect content safety
    detection_result = content_safety.detect(media_type, content, blocklists)

    # Set the reject thresholds for each category
    reject_thresholds = {
        Category.Hate: 4,
        Category.SelfHarm: 4,
        Category.Sexual: 6,
        Category.Violence: 4,
    }

    # Make a decision based on the detection result and reject thresholds
    decision_result = content_safety.make_decision(detection_result, reject_thresholds)
    
    if decision_result.suggested_action == Action.Accept:
        return True
    
    return False