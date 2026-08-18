"""Ollama local-LLM integration for the Data Assistant.

Connects to a locally running Ollama server, lists live models, and answers
user queries EXCLUSIVELY within the aviation / power-grid safety domain of this
project. Out-of-domain questions are politely refused.
"""
import logging
import time

import httpx

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are SafetyNLP, a senior aviation and power-grid safety analyst. "
    "Your ONLY scope is aviation incident reports (NASA ASRS) and power-grid "
    "event analysis (NERC): flight safety, runway incidents, engine failures, "
    "bird strikes, weather hazards, air traffic control, power outages, "
    "blackouts, grid disturbances, substations, transmission lines and related "
    "safety procedures.\n\n"
    "Rules:\n"
    "1. Answer only questions about THIS domain (aviation & power-grid safety).\n"
    "2. If the question is unrelated (weather forecast, sports, recipes, "
    "programming, general knowledge), reply that you can only assist with "
    "aviation and power-grid safety analysis for this project.\n"
    "3. Keep answers concise, factual and safety-focused. When relevant, "
    "suggest concrete safety recommendations and mitigation actions.\n"
    "4. Never invent statistics or incident records. Refer to the dataset "
    "statistics provided in the context when they are available.\n"
)

# Keywords used to detect out-of-domain questions before the LLM is invoked.
DOMAIN_KEYWORDS = [
    "aviation", "aircraft", "airplane", "flight", "pilot", "cockpit", "airport",
    "runway", "takeoff", "take-off", "landing", "approach", "engine", "turbine",
    "jet", "plane", "asrs", "ntsb", "atc", "air traffic", "altitude", "bird",
    "weather", "turbulence", "wind shear", "icing", "fuel", "hydraulic",
    "decompression", "emergency", "mayday", "navigation", "avionics",
    "power grid", "powergrid", "electricity", "electrical", "grid", "substation",
    "transmission", "power cut", "power outage", "blackout", "brownout",
    "outage", "nerc", "ukpn", "utility", "energy", "distribution",
    "customer", "load shed", "voltage", "frequency", "disturbance",
    "northeast blackout", "arctic", "hurricane", "storm", "snowstorm",
    "safety", "incident", "accident", "risk", "hazard", "report", "dataset",
    "class", "category", "classification", "model", "monitor", "alert",
    "evidence", "rag", "narrative", "anomaly",
]

OUT_OF_SCOPE_REPLY = (
    "I can only help with questions about this project's domain: aviation "
    "incident reports (NASA ASRS) and power-grid event analysis (NERC). "
    "Please ask about flight safety, engine failures, runway incidents, power "
    "outages, grid disturbances, or the dataset itself."
)


class OllamaStatus:
    connected: bool
    base_url: str
    model: str
    models: list

    def __init__(self, connected: bool = False, base_url: str = "",
                 model: str = "", models: list = None):
        self.connected = connected
        self.base_url = base_url
        self.model = model
        self.models = models or []

    def to_dict(self) -> dict:
        return {
            "connected": self.connected,
            "base_url": self.base_url,
            "model": self.model,
            "models": self.models,
            "default_model": settings.OLLAMA_MODEL,
        }


class OllamaService:
    """Thin client over the Ollama HTTP API with cached status."""

    def __init__(self):
        self._status = OllamaStatus()
        self._last_check = 0.0

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=settings.OLLAMA_BASE_URL.rstrip("/"),
            timeout=settings.OLLAMA_TIMEOUT,
        )

    def get_status(self, force: bool = False) -> OllamaStatus:
        """Return cached status; refresh if the TTL expired."""
        now = time.monotonic()
        if not force and self._status.connected and now - self._last_check < settings.OLLAMA_STATUS_TTL:
            return self._status
        if force or now - self._last_check >= settings.OLLAMA_STATUS_TTL:
            self._refresh()
        return self._status

    def _refresh(self) -> None:
        self._last_check = time.monotonic()
        try:
            with self._client() as client:
                resp = client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()
            raw_models = [m.get("name", "") for m in data.get("models", [])]
            models = sorted(m for m in raw_models if m)
            preferred = settings.OLLAMA_MODEL
            if preferred not in models:
                # Accept "llama3" -> "llama3:latest" style matches
                preferred = next(
                    (m for m in models if m.startswith(settings.OLLAMA_MODEL + ":")
                     or m == settings.OLLAMA_MODEL or m.startswith(settings.OLLAMA_MODEL)),
                    settings.OLLAMA_MODEL,
                )
            model = preferred if preferred in models else (models[0] if models else settings.OLLAMA_MODEL)
            self._status = OllamaStatus(
                connected=True,
                base_url=settings.OLLAMA_BASE_URL,
                model=model,
                models=models,
            )
            logger.info("Ollama connected: %d model(s), using '%s'", len(models), model)
        except Exception as exc:
            self._status = OllamaStatus(
                connected=False,
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
            )
            logger.debug("Ollama not reachable: %s: %s", type(exc).__name__, exc)

    def is_domain_relevant(self, query: str) -> bool:
        """Quick deterministic check: is the question inside this project's domain?"""
        q = query.lower()
        return any(k in q for k in DOMAIN_KEYWORDS)

    def chat(self, query: str, model: str = None,
             context: str = None) -> tuple[bool, str]:
        """Send a domain-constrained chat to Ollama.

        Returns (handled, reply). When ``handled`` is False the caller should
        fall back to the rule-based analyst.
        """
        status = self.get_status()
        if not status.connected:
            return False, "Ollama is not connected"

        if not self.is_domain_relevant(query):
            return True, OUT_OF_SCOPE_REPLY

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": query})

        payload = {
            "model": model or status.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 800},
        }

        try:
            with self._client() as client:
                resp = client.post("/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
            reply = (data.get("message") or {}).get("content") or ""
            return True, reply.strip()
        except Exception as exc:
            logger.warning("Ollama chat failed: %s: %s", type(exc).__name__, exc)
            return False, ""

    def build_context(self, dataset_summary: dict = None,
                      domain_text: str = None) -> str:
        """Optional context block fed to the LLM (dataset stats)."""
        parts = [
            "Project context: Safety NLP Pipeline analyzes aviation incident "
            "reports (NASA ASRS) and power-grid event analyses (NERC)."
        ]
        if dataset_summary and dataset_summary.get("total_reports"):
            parts.append(
                f"Loaded dataset: {dataset_summary.get('total_reports')} reports "
                f"across {list((dataset_summary.get('domains') or {}).keys())} "
                f"with {dataset_summary.get('anomaly_classes')} anomaly classes."
            )
        if domain_text:
            parts.append(domain_text)
        return "\n".join(parts)


ollama_service = OllamaService()
