import httpx
from services.memory.static_memory import get_static_memory

async def get_ai_triage(
    location: str,
    pressure: float,
    classification: str,
    anomaly_data: dict,
    operator_context: str = "",
    session_memory: str = "",
) -> str:
    """
    Calls Claude API when anomaly_flag = True.
    Returns 2-3 sentence triage assessment.
    Only called on anomalous readings — not every ingest.
    """
    static_ctx  = get_static_memory(location)

    prompt = f"""You are a crowd safety analyst for a Gujarat pilgrimage monitoring system.

LOCATION MEMORY:
{static_ctx}

SESSION EVENTS (this run):
{session_memory or 'No prior events this session.'}

CURRENT SITUATION:
- Location: {location}
- Pressure index: {pressure}/100
- ML classification: {classification}
- Anomaly z-score: {anomaly_data['z_score']:.2f} (statistically unusual flow pattern)
- Severity: {anomaly_data['anomaly_severity']}
- Operator note: {operator_context or 'None provided'}

In exactly 2-3 sentences: what is likely happening, what is the primary risk, which agency should act first. Be specific and direct. No hedging."""

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
    result = resp.json()
    return result["content"][0]["text"]
