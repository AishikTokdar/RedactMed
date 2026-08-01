"""Agent wiring for model execution supporting Amazon Bedrock (Claude, Nova, Llama, Mistral) and alternative providers via Pydantic-AI."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import logfire
from botocore.config import Config
from pydantic_ai import Agent, ToolOutput
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.providers.bedrock import BedrockProvider

from agent.models import CompactAgentResponse
from agent.prompt import SYSTEM_PROMPT

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    if os.getenv("ENVIRONMENT") == 'local':
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        load_dotenv(env_path)
except ImportError:
    pass

# Disable Logfire scrubbing for prompt and system_instructions attributes
def _scrubbing_callback(m: logfire.ScrubMatch):
    return m.value

_scrubbing_options = logfire.ScrubbingOptions(callback=_scrubbing_callback)

# Configure logfire instrumentation
logfire.configure(scrubbing=_scrubbing_options)
logfire.instrument_pydantic_ai()

# Determine model provider (default: bedrock)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock").lower()
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    os.getenv("MODEL_NAME", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
)

if LLM_PROVIDER == "bedrock":
    # Initialize boto3 session and Bedrock client
    # Disable boto3 retries - let worker-level retry handle throttling with proper backoff
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    session = boto3.Session(region_name=aws_region)
    bedrock_config = Config(retries={"max_attempts": 0})
    bedrock_client = session.client("bedrock-runtime", config=bedrock_config)

    # Enable prompt caching for Anthropic models on Bedrock
    is_anthropic = "anthropic" in MODEL_ID.lower()
    bedrock_settings = BedrockModelSettings(
        bedrock_cache_instructions=is_anthropic,
        bedrock_cache_tool_definitions=is_anthropic,
    )

    bedrock_model = BedrockConverseModel(
        MODEL_ID,
        provider=BedrockProvider(bedrock_client=bedrock_client),
    )

    pii_agent = Agent[None, CompactAgentResponse](
        model=bedrock_model,
        instructions=SYSTEM_PROMPT,
        output_type=ToolOutput(CompactAgentResponse),
        model_settings=bedrock_settings if is_anthropic else None,
    )

elif LLM_PROVIDER in ("openai", "azure_openai"):
    # OpenAI model support (e.g., MODEL_NAME="gpt-4o-mini")
    pii_agent = Agent[None, CompactAgentResponse](
        model=f"openai:{MODEL_ID}",
        instructions=SYSTEM_PROMPT,
        output_type=ToolOutput(CompactAgentResponse),
    )

elif LLM_PROVIDER == "gemini":
    # Google Gemini model support (e.g., MODEL_NAME="gemini-1.5-flash")
    pii_agent = Agent[None, CompactAgentResponse](
        model=f"google-gla:{MODEL_ID}",
        instructions=SYSTEM_PROMPT,
        output_type=ToolOutput(CompactAgentResponse),
    )

elif LLM_PROVIDER == "ollama":
    # Local Ollama model support (100% Free local execution, e.g. MODEL_NAME="llama3.2")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    pii_agent = Agent[None, CompactAgentResponse](
        model=f"openai:{MODEL_ID}",
        instructions=SYSTEM_PROMPT,
        output_type=ToolOutput(CompactAgentResponse),
    )

else:
    # Fallback to direct model string for custom Pydantic-AI models
    pii_agent = Agent[None, CompactAgentResponse](
        model=MODEL_ID,
        instructions=SYSTEM_PROMPT,
        output_type=ToolOutput(CompactAgentResponse),
    )