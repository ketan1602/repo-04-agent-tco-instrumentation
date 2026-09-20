from __future__ import annotations

import os

import truststore

truststore.inject_into_ssl()

_BASE_URL = os.environ.get("AIREFINERY_BASE_URL", "https://sdk.airefinery.accenture.com/distiller")
_DEFAULT_MODEL = os.environ.get("AIR_MODEL", "openai/gpt-oss-120b")
_TEMPERATURE = 0.1


async def complete(system_prompt: str, user_msg: str) -> str:
    """Call the AI Refinery chat completion API and return the response content."""
    from air import AsyncAIRefinery

    api_key = os.environ.get("AIREFINERY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "AIREFINERY_API_KEY must be set. "
            "See .env.example and https://sdk.airefinery.accenture.com/distiller/model_catalog/"
        )
    client = AsyncAIRefinery(api_key=api_key, base_url=_BASE_URL)
    response = await client.chat.completions.create(
        model=_DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=_TEMPERATURE,
    )
    return response.choices[0].message.content
