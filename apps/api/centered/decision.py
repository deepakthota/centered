"""Versioned, deterministic development policy. Catalog is NOT evidence-reviewed."""

from .schemas import CheckIn

POLICY_VERSION = "manual-demo-v1"
CATALOG_VERSION = "unreviewed-demo-v1"
ACTIONS = {
    "pause": {"title": "Take a quiet two-minute pause", "minutes": 2},
    "walk": {"title": "Take a gentle five-minute walk", "minutes": 5},
    "break": {"title": "Step away from your screen for two minutes", "minutes": 2},
}


def choose_action(context: CheckIn) -> dict:
    if context.available_minutes < 2:
        return {
            "action": None,
            "reason": "The current catalog has no action that fits your available time.",
            "policy_version": POLICY_VERSION,
            "catalog_version": CATALOG_VERSION,
            "evidence_status": "pending_review",
            "input_source": "manual",
        }
    low_energy = context.energy is not None and context.energy <= 2
    high_stress = context.stress is not None and context.stress >= 4
    short_sleep = context.sleep_hours is not None and context.sleep_hours < 6
    if low_energy or high_stress or short_sleep:
        key = "pause"
        factors = []
        if low_energy:
            factors.append("low energy")
        if high_stress:
            factors.append("high stress")
        if short_sleep:
            factors.append("short sleep")
        reason = f"You reported {', '.join(factors)}. This option asks for little effort."
    elif context.allow_movement and context.available_minutes >= 5:
        key = "walk"
        reason = "You allowed movement and have at least five minutes available."
    else:
        key = "break"
        reason = "This short option fits your time without requiring exercise."
    return {
        "action": {"key": key, **ACTIONS[key]},
        "reason": reason,
        "policy_version": POLICY_VERSION,
        "catalog_version": CATALOG_VERSION,
        "evidence_status": "pending_review",
        "input_source": "manual",
    }
