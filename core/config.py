
import re
from typing import Dict, Any, Optional
from google import genai
from google.genai.types import (
    GenerateContentConfig, 
    ThinkingConfig, 
    HttpOptions
)
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv(override=True)
async def vertexai_model(
    system: str,
    user: str,
    temperature: float = None,
    model: str = "gemini-2.5-flash-preview-09-2025",
    schema: Optional[Dict[str, Any]] = None,
    thinking_config: Optional[Dict[str, Any] | bool] = None,
    extra_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Calls a Vertex AI Gemini model using service account authentication and returns cleaned response.

    Requires the following environment variables:
        GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON key file
        GOOGLE_CLOUD_PROJECT: Your GCP project ID
        GOOGLE_CLOUD_LOCATION: GCP region (e.g., 'us-central1')

    Args:
        system: System instruction that defines model behavior
        user: User prompt/message
        temperature: Sampling temperature (0.0-2.0)
        model: Model ID (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash-001')
        schema: Optional JSON schema for structured output
        extra_config: Optional additional config parameters (safety_settings, max_tokens, etc.)

    Returns:
        Cleaned response text with markdown and thinking tokens stripped
    """
    
    attempts = 3

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    service_account_file = "auth.json"

    if not service_account_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable must be set to the path of your service account JSON file")

    credentials = Credentials.from_service_account_file(service_account_file, scopes=scopes)

    client = genai.Client(
        vertexai=True,
        project="brae-v2",
        location="global",
        credentials=credentials,
        http_options=HttpOptions(api_version="v1")
    )
    
    for _ in range(attempts):
        try:
            config_params = {
                "system_instruction": [system] if system else None,
            }
            
            if temperature is not None:
                config_params["temperature"] = temperature
            
            # config_params["tools"] = [
            #         # Tool(google_search=GoogleSearch()),
            #     {"url_context": {}},
            # ]
            if thinking_config:
                config_params["thinking_config"] = ThinkingConfig(thinking_budget=8192, include_thoughts=True)

            if schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = schema
            
            if extra_config:
                config_params.update(extra_config)
            
            config = GenerateContentConfig(**config_params)
            
            response = await client.aio.models.generate_content(
                model=model,
                contents=user,
                config=config,
            )

            print(response.text)
            
            if not response.text:
                continue
            
            content = re.sub(r'^.*?</think>\s*|```json\s*|\s*```', '', response.text, flags=re.DOTALL).strip()
            
            return content
            
        except Exception as e:
            if _ == attempts - 1:
                raise e
            continue
    
    return ""