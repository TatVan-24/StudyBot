"""Model Rotator — Track rate limits, rotate models, log model execution.

Supports unified OpenAI-compatible client endpoint (api.mwapi.dev/v1).
"""
import logging
import os
import re
import time
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("model_rotator")

# ── MODEL REGISTRY (Free Plan Limits from Provider) ─────────────────────────
MODEL_REGISTRY: List[Dict[str, Any]] = [
    {
        "name": os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b"),
        "rpm_limit": 30,
        "tpm_limit": 8000,
        "priority": 1,
    },
    {
        "name": "openai/gpt-oss-20b",
        "rpm_limit": 30,
        "tpm_limit": 8000,
        "priority": 2,
    },
    {
        "name": "canopylabs/orpheus-v1-english",
        "rpm_limit": 10,
        "tpm_limit": 1200,
        "priority": 3,
    },
]


# ── QUOTA TRACKER ────────────────────────────────────────────────────────────
class QuotaTracker:
    def __init__(self, model_name: str, limit: int):
        self.model_name = model_name
        self.limit = limit
        self.count = limit
        self.reset_at = time.time() + 60
        self.lock = Lock()

    def _maybe_reset(self):
        if time.time() >= self.reset_at:
            self.count = self.limit
            self.reset_at = time.time() + 60

    def consume(self, amount: int = 1) -> int:
        with self.lock:
            self._maybe_reset()
            self.count = max(0, self.count - amount)
            return self.count

    def remaining(self) -> int:
        with self.lock:
            self._maybe_reset()
            return self.count

    def is_low(self, threshold: int = 5) -> bool:
        return self.remaining() < threshold

    def reset(self):
        with self.lock:
            self.count = self.limit
            self.reset_at = time.time() + 60


_trackers: Dict[str, QuotaTracker] = {}


def _get_tracker(model_name: str, limit: int) -> QuotaTracker:
    if model_name not in _trackers:
        _trackers[model_name] = QuotaTracker(model_name, limit)
    return _trackers[model_name]


# ── MODEL LOGGING ────────────────────────────────────────────────────────────
def log_model_event(event: str, from_model: Optional[str] = None, to_model: Optional[str] = None, reason: Optional[str] = None):
    print(f"[MODEL_ROTATOR] event={event} from={from_model} to={to_model} reason={reason}")
    logger.info(
        "[MODEL_ROTATOR] event=%s from=%s to=%s reason=%s",
        event, from_model, to_model, reason,
    )


def log_model_call(model_name: str, attempt: int, latency_ms: int, status: str):
    print(f"[MODEL_CALL] model={model_name} attempt={attempt} latency_ms={latency_ms} status={status}")
    logger.info(
        "[MODEL_CALL] model=%s attempt=%d latency_ms=%d status=%s",
        model_name, attempt, latency_ms, status,
    )


# ── MODEL PICKER ─────────────────────────────────────────────────────────────
def pick_model(current_model_name: Optional[str] = None, threshold: int = 5) -> Dict[str, Any]:
    """
    Trả về model khả dụng tiếp theo.
    - Nếu model hiện tại còn count >= threshold -> giữ nguyên.
    - Nếu count < threshold -> chuyển sang model priority kế tiếp.
    """
    if current_model_name is not None:
        current = next(
            (m for m in MODEL_REGISTRY if m["name"] == current_model_name),
            None,
        )
        if current is not None:
            limit = current.get("rpm_limit", 30)
            tracker = _get_tracker(current_model_name, limit)
            if not tracker.is_low(threshold):
                return current
            
            log_model_event(
                event="rotate",
                from_model=current_model_name,
                reason=f"count={tracker.remaining()} < {threshold}",
            )

    for model in sorted(MODEL_REGISTRY, key=lambda m: m["priority"]):
        limit = model.get("rpm_limit", 30)
        tracker = _get_tracker(model["name"], limit)
        if not tracker.is_low(threshold):
            return model

    log_model_event(
        event="exhausted",
        from_model=current_model_name,
        reason="all models below threshold",
    )
    return MODEL_REGISTRY[0]


# ── LLM CALL WRAPPER WITH ROTATION ───────────────────────────────────────────
def call_with_rotation(
    client: Any,
    messages: List[Dict[str, str]],
    max_attempts: int = 5,
    threshold: int = 5,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Tuple[str, str]:
    """
    Gọi LLM với cơ chế Rotation + Quota Tracking.
    - RPM count < threshold -> đổi model
    - HTTP 429 -> lập tức đổi sang model tiếp theo
    - Ghi log model_name và latency
    Returns: (answer_text, model_used)
    """
    current_model_name = None

    for attempt in range(1, max_attempts + 1):
        model_info = pick_model(current_model_name, threshold=threshold)
        model_name = model_info["name"]
        current_model_name = model_name

        limit = model_info.get("rpm_limit", 30)
        tracker = _get_tracker(model_name, limit)
        tracker.consume()

        log_model_event(
            event="call",
            to_model=model_name,
            reason=f"attempt={attempt}, remaining={tracker.remaining()}",
        )

        start = time.time()
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            answer = response.choices[0].message.content
            latency_ms = int((time.time() - start) * 1000)
            log_model_call(model_name, attempt, latency_ms, "success")
            return answer, model_name

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            err = str(e)

            if "429" in err or "rate limit" in err.lower() or "quota" in err.lower():
                log_model_call(model_name, attempt, latency_ms, "429")
                log_model_event(
                    event="429",
                    from_model=model_name,
                    reason=err[:120],
                )
                tracker.reset()
                current_model_name = None
                time.sleep(1.0)
                continue

            log_model_call(model_name, attempt, latency_ms, "error")
            raise e

    raise RuntimeError("call_with_rotation: All fallback models exhausted due to rate limits.")
