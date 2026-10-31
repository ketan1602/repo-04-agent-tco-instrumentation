from __future__ import annotations

import os

import openai

_BASE_URL = os.environ.get("LLM_BASE_URL", "").strip() or None
_DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_TEMPERATURE = 0.1


async def complete(system_prompt: str, user_msg: str) -> str:
    """Call any OpenAI-compatible chat API and return the response content."""
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY must be set. See .env.example."
        )
    client = openai.AsyncOpenAI(api_key=api_key, base_url=_BASE_URL)
    response = await client.chat.completions.create(
        model=_DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=_TEMPERATURE,
    )
    return response.choices[0].message.content
