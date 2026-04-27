import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from config import EPISODE_CSV_PATH, OUTPUT_DIR, PROMPT_HISTORY_JSON_PATH, PROMPT_JSON_PATH


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_prompt_json(prompt_pack: Dict[str, str], path: Path = PROMPT_JSON_PATH):
    ensure_output_dir()
    path.write_text(json.dumps(prompt_pack, ensure_ascii=False, indent=2), encoding="utf-8")


def save_prompt_history_json(logs: List[Dict[str, Any]], path: Path = PROMPT_HISTORY_JSON_PATH):
    ensure_output_dir()
    prompt_logs = [
        {
            "episode": log["episode"],
            "action": log["action"],
            "player_input": log["state"].player_input,
            "prompt_pack": log["prompt_pack"],
        }
        for log in logs
    ]
    path.write_text(json.dumps(prompt_logs, ensure_ascii=False, indent=2), encoding="utf-8")


def export_episode_logs_csv(logs: List[Dict[str, Any]], path: Path = EPISODE_CSV_PATH):
    ensure_output_dir()
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "episode",
                "action",
                "reward",
                "player_input",
                "chief_lines",
                "system_lines",
                "weapon_given",
                "dialogue_step",
                "line_count_add",
            ],
        )
        writer.writeheader()

        for log in logs:
            result = log["result"]
            state_update = result.get("state_update", {})
            writer.writerow(
                {
                    "episode": log["episode"],
                    "action": log["action"],
                    "reward": f"{log['reward']:.3f}",
                    "player_input": log["state"].player_input,
                    "chief_lines": " | ".join(result.get("chief_lines", [])),
                    "system_lines": " | ".join(result.get("system_lines", [])),
                    "weapon_given": state_update.get("weapon_given", False),
                    "dialogue_step": state_update.get("dialogue_step", ""),
                    "line_count_add": state_update.get("line_count_add", 0),
                }
            )
