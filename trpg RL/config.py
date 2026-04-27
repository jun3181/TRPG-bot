import os
from pathlib import Path

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

EPISODES = int(os.getenv("TRPG_EPISODES", "1000"))
LEARNING_RATE = float(os.getenv("TRPG_LEARNING_RATE", "0.1"))
EPSILON_START = float(os.getenv("TRPG_EPSILON_START", "0.30"))
EPSILON_END = float(os.getenv("TRPG_EPSILON_END", "0.05"))

USE_OPENAI_FOR_TRAINING = os.getenv("TRPG_USE_OPENAI_FOR_TRAINING", "false").lower() == "true"
USE_OPENAI_FOR_FINAL_TEST = os.getenv("TRPG_USE_OPENAI_FOR_FINAL_TEST", "false").lower() == "true"

OUTPUT_DIR = Path("trpg RL/outputs")
PROMPT_JSON_PATH = OUTPUT_DIR / "latest_prompt_pack.json"
PROMPT_HISTORY_JSON_PATH = OUTPUT_DIR / "prompt_packs.json"
EPISODE_CSV_PATH = OUTPUT_DIR / "episode_dialogues.csv"

PLAYER_INPUT_SAMPLES = [
    "네, 알겠습니다.",
    "좋아요. 뭘 하면 되죠?",
    "무기가 필요한가요?",
    "빨리 알려주세요.",
    "튜토리얼은 처음이에요.",
    "싫은데요?",
    "일단 해볼게요.",
    "촌장님, 저는 무엇을 해야 하나요?",
    "무기부터 주세요.",
    "알겠어요.",
]

ACTIONS = {
    "fast_weapon_grant": {
        "description": "가장 빠르게 무기 지급까지 진행하는 프롬프트를 만들게 한다.",
        "target": "2문장 이내로 무기를 지급하고, 시스템 메시지에 '무기를 지급했습니다!'를 포함한다.",
    },
    "friendly_tutorial": {
        "description": "친절하고 부드러운 튜토리얼 말투의 프롬프트를 만들게 한다.",
        "target": "플레이어 반응을 받아주되, 무기 지급을 자연스럽게 진행한다.",
    },
    "immersive_intro": {
        "description": "세계관 몰입감을 살리는 프롬프트를 만들게 한다.",
        "target": "분위기를 살리지만 5줄 제한을 지킨다.",
    },
    "adaptive_reply": {
        "description": "플레이어 입력을 강하게 반영하는 프롬프트를 만들게 한다.",
        "target": "플레이어 말에 반응하면서 무기 지급까지 진행한다.",
    },
    "strict_goal": {
        "description": "목표 달성을 최우선으로 하는 강한 제약 프롬프트를 만들게 한다.",
        "target": "반드시 이번 응답에서 무기를 지급하고, '무기를 지급했습니다!'를 출력한다.",
    },
}

DIALOGUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "chief_lines": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 2},
        "system_lines": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 1},
        "state_update": {
            "type": "object",
            "properties": {
                "weapon_given": {"type": "boolean"},
                "dialogue_step": {"type": "string"},
                "line_count_add": {"type": "integer"},
            },
            "required": ["weapon_given", "dialogue_step", "line_count_add"],
            "additionalProperties": False,
        },
    },
    "required": ["chief_lines", "system_lines", "state_update"],
    "additionalProperties": False,
}
