from typing import Any, Dict

from models import DialogueState


def calculate_reward(state: DialogueState, result: Dict[str, Any]) -> float:
    chief_lines = result.get("chief_lines", [])
    system_lines = result.get("system_lines", [])
    state_update = result.get("state_update", {})

    weapon_given = bool(state_update.get("weapon_given", False))
    total_lines = state.line_count + len(chief_lines) + len(system_lines)
    line_limit_success = total_lines <= state.max_line_count
    required_sentence_success = "무기를 지급했습니다" in " ".join(system_lines)
    has_weapon_word = "무기" in " ".join(chief_lines) or "검" in " ".join(chief_lines)

    reward = 0.0
    if weapon_given:
        reward += 0.45
    if line_limit_success:
        reward += 0.25
    if required_sentence_success:
        reward += 0.20
    if has_weapon_word:
        reward += 0.10

    return min(reward, 1.0)
