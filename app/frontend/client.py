"""Small HTTP client used by Streamlit; it never imports the LangGraph agent."""
from __future__ import annotations
import os
import httpx
from dotenv import load_dotenv

def submit_research(payload: dict, client: httpx.Client | None = None) -> dict:
    load_dotenv()
    base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    timeout_seconds = float(os.getenv("BACKEND_TIMEOUT_SECONDS", "90"))
    try:
        response = (client or httpx.Client(timeout=timeout_seconds)).post(f"{base_url}/research", json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as error:
        raise RuntimeError("The research request timed out. Please try again.") from error
    except httpx.RequestError as error:
        raise RuntimeError("The FastAPI backend is unavailable. Start it and try again.") from error
    except httpx.HTTPStatusError as error:
        raise RuntimeError(f"The backend returned an error ({error.response.status_code}).") from error
    except ValueError as error:
        raise RuntimeError("The backend returned an invalid response.") from error
    if not isinstance(data, dict) or "answer" not in data:
        raise RuntimeError("The backend returned an unexpected response.")
    return data
