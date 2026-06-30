"""
Ollama client — wraps glm-4.7-flash for narrative quality scoring.

Uses the OpenAI-compatible Ollama API endpoint.
Falls back to Claude API (Anthropic) if Ollama is unreachable.

SECURITY: All text reaching this module must already be PII-scrubbed.
Never pass raw report text here — run pii_scrubber.py first.
"""
import json
import logging

import anthropic
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_ollama_client: AsyncOpenAI | None = None
_anthropic_client: anthropic.AsyncAnthropic | None = None

NARRATIVE_SYSTEM_PROMPT = """You are an expert appraisal reviewer evaluating UAD appraisal report \
nnarrative quality for USPAP compliance and GSE acceptability.

Score the following commentary on 0-100 based on:
- Specificity (not boilerplate language)
- Support for value conclusion
- Market condition analysis depth
- Internal consistency
- Absence of unsupported statements

Return ONLY valid JSON in this exact format:
{"score": <integer 0-100>, "flags": [{"field": "<field name>", "issue": "<description>"}]}

Return an empty flags array if no issues found."""


def _get_ollama() -> AsyncOpenAI:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = AsyncOpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        )
    return _ollama_client


def _get_anthropic() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


async def score_narrative(scrubbed_text: str) -> dict:
    """
    Score appraisal narrative quality using Ollama (glm-4.7-flash).
    Falls back to Claude API if Ollama unreachable.

    Args:
        scrubbed_text: PII-scrubbed narrative text. Must not contain
                       real names, addresses, or financial identifiers.

    Returns:
        {"score": int, "flags": [{"field": str, "issue": str}]}
    """
    try:
        return await _score_with_ollama(scrubbed_text)
    except Exception as e:
        logger.warning(
            "Ollama unreachable, falling back to Claude API",
            extra={"error": str(e)},
        )
        if settings.anthropic_api_key:
            return await _score_with_claude(scrubbed_text)
        logger.error("Both Ollama and Claude API unavailable — returning fallback score")
        return {
            "score": 50,
            "flags": [{"field": "narrative", "issue": "AI scorer unavailable — manual review required"}],
        }


async def _score_with_ollama(scrubbed_text: str) -> dict:
    response = await _get_ollama().chat.completions.create(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
            {"role": "user", "content": scrubbed_text},
        ],
        temperature=0.1,
        max_tokens=512,
    )
    return _parse_score_response(response.choices[0].message.content)


async def _score_with_claude(scrubbed_text: str) -> dict:
    response = await _get_anthropic().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=NARRATIVE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": scrubbed_text}],
    )
    return _parse_score_response(response.content[0].text)


def _parse_score_response(raw: str) -> dict:
    """Parse JSON score response, return safe fallback on parse error."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        score = max(0, min(100, int(result.get("score", 50))))
        flags = result.get("flags", [])
        return {"score": score, "flags": flags}
    except Exception:
        logger.warning("Failed to parse AI score response", extra={"raw": raw[:200]})
        return {"score": 50, "flags": [{"field": "narrative", "issue": "Score parse error — manual review"}]}
