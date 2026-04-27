import json
from typing import Any, Dict

from config import ACTIONS, DIALOGUE_OUTPUT_SCHEMA, MODEL
from models import DialogueState


class PromptGenerator:
    def __init__(self, use_openai: bool):
        self.use_openai = use_openai

    def generate(self, state: DialogueState, action_name: str) -> Dict[str, str]:
        if self.use_openai:
            return self._call_api(state, action_name)
        return self._mock(state, action_name)

    def _call_api(self, state: DialogueState, action_name: str) -> Dict[str, str]:
        from openai import OpenAI

        client = OpenAI()
        action = ACTIONS[action_name]

        system_prompt = """
너는 TRPG 봇 실험을 위한 Prompt Generator Agent다.
너의 역할은 최종 대사를 쓰는 것이 아니라,
Dialogue Generator GPT에게 전달할 프롬프트를 작성하는 것이다.
반드시 한국어 중심의 프롬프트를 만든다.
""".strip()

        user_prompt = f"""
현재 실험 목표:
- 시작마을 촌장 NPC가 플레이어에게 튜토리얼을 안내한다.
- 전체 촌장 대화는 5줄 이내여야 한다.
- 이번 응답에서 기본 무기를 지급해야 한다.
- 최종 출력 어딘가에 반드시 \"무기를 지급했습니다!\" 문장이 나오게 해야 한다.

현재 State:
- scene_id: {state.scene_id}
- npc_id: {state.npc_id}
- player_nickname: {state.player_nickname}
- dialogue_step: {state.dialogue_step}
- line_count: {state.line_count}
- max_line_count: {state.max_line_count}
- weapon_given: {state.weapon_given}
- quest_offered: {state.quest_offered}
- player_input: {state.player_input}

선택된 Prompt Action:
- action_name: {action_name}
- description: {action['description']}
- target: {action['target']}

Dialogue Generator에게 줄 프롬프트 3개를 작성하라:
1. system_prompt
2. developer_prompt
3. user_prompt
""".strip()

        response = client.responses.create(
            model=MODEL,
            input=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "prompt_pack",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "system_prompt": {"type": "string"},
                            "developer_prompt": {"type": "string"},
                            "user_prompt": {"type": "string"},
                        },
                        "required": ["system_prompt", "developer_prompt", "user_prompt"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        return json.loads(response.output_text)

    def _mock(self, state: DialogueState, action_name: str) -> Dict[str, str]:
        action = ACTIONS[action_name]
        return {
            "system_prompt": "너는 한국어 TRPG 시작마을 촌장 NPC다. 출력은 JSON만.",
            "developer_prompt": (
                f"선택된 전략: {action_name}\n"
                f"전략 설명: {action['description']}\n"
                f"전략 목표: {action['target']}\n"
                "chief_lines는 1~2줄, system_lines는 1줄. 무기 지급 문구 포함."
            ),
            "user_prompt": (
                f"플레이어 입력: {state.player_input}\n"
                f"{state.player_nickname}에게 무기를 지급했습니다! 문구가 포함되게 생성."
            ),
        }


class DialogueGenerator:
    def __init__(self, use_openai: bool):
        self.use_openai = use_openai

    def generate(self, state: DialogueState, action_name: str, prompt_pack: Dict[str, str]) -> Dict[str, Any]:
        if self.use_openai:
            return self._call_api(prompt_pack)
        return self._mock(state, action_name)

    def _call_api(self, prompt_pack: Dict[str, str]) -> Dict[str, Any]:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": prompt_pack["system_prompt"]},
                {"role": "developer", "content": prompt_pack["developer_prompt"]},
                {"role": "user", "content": prompt_pack["user_prompt"]},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "chief_dialogue_result",
                    "strict": True,
                    "schema": DIALOGUE_OUTPUT_SCHEMA,
                }
            },
        )
        return json.loads(response.output_text)

    def _mock(self, state: DialogueState, action_name: str) -> Dict[str, Any]:
        chief_lines = [
            f"'{state.player_input}'라, 좋은 대답일세.",
            "그럼 바로 이 기본 무기를 받게나.",
        ]

        if action_name == "fast_weapon_grant":
            chief_lines = ["좋네. 군더더기 없이 바로 지급하겠네.", "자, 기본 무기를 받게나."]

        return {
            "chief_lines": chief_lines,
            "system_lines": [f"{state.player_nickname}에게 무기를 지급했습니다!"],
            "state_update": {
                "weapon_given": True,
                "dialogue_step": "weapon_given",
                "line_count_add": 3,
            },
        }
