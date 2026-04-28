import json
from urllib import error, request
from typing import Any, Dict

from config import ACTIONS, API_PROVIDER, DIALOGUE_OUTPUT_SCHEMA, GEMINI_MODEL, MODEL
from models import DialogueState


class ApiQuotaExceededError(RuntimeError):
    """API 호출 한도 초과 시 학습을 중단하기 위한 예외."""


class PromptGenerator:
    def __init__(self, use_openai: bool):
        self.use_openai = use_openai

    def generate(self, state: DialogueState, action_name: str) -> Dict[str, str]:
        if self.use_openai:
            return self._call_api(state, action_name)
        return self._mock(state, action_name)

    def _call_api(self, state: DialogueState, action_name: str) -> Dict[str, str]:
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

반드시 JSON 객체 하나만 출력:
{{
  \"system_prompt\": string,
  \"developer_prompt\": string,
  \"user_prompt\": string
}}
""".strip()

        if API_PROVIDER == "gemini":
            payload = _gemini_generate_json(
                model=GEMINI_MODEL,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "system_prompt": {"type": "string"},
                        "developer_prompt": {"type": "string"},
                        "user_prompt": {"type": "string"},
                    },
                    "required": ["system_prompt", "developer_prompt", "user_prompt"],
                },
            )
            return payload

        client = _build_openai_compatible_client()
        prompt_pack_schema = {
            "type": "object",
            "properties": {
                "system_prompt": {"type": "string"},
                "developer_prompt": {"type": "string"},
                "user_prompt": {"type": "string"},
            },
            "required": ["system_prompt", "developer_prompt", "user_prompt"],
            "additionalProperties": False,
        }
        response = _create_structured_response(
            client=client,
            model=MODEL,
            input_messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            schema_name="prompt_pack",
            schema=prompt_pack_schema,
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
        if API_PROVIDER == "gemini":
            return _gemini_generate_json(
                model=GEMINI_MODEL,
                system_prompt=prompt_pack["system_prompt"],
                user_prompt=(
                    prompt_pack["developer_prompt"]
                    + "\n\n"
                    + prompt_pack["user_prompt"]
                    + "\n\n반드시 JSON 객체만 출력하라."
                ),
                response_schema=DIALOGUE_OUTPUT_SCHEMA,
            )

        client = _build_openai_compatible_client()
        response = _create_structured_response(
            client=client,
            model=MODEL,
            input_messages=[
                {"role": "system", "content": prompt_pack["system_prompt"]},
                {"role": "developer", "content": prompt_pack["developer_prompt"]},
                {"role": "user", "content": prompt_pack["user_prompt"]},
            ],
            schema_name="chief_dialogue_result",
            schema=DIALOGUE_OUTPUT_SCHEMA,
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



def _build_openai_compatible_client():
    from openai import OpenAI

    if API_PROVIDER == "groq":
        return OpenAI(
            api_key=_require_groq_api_key(),
            base_url="https://api.groq.com/openai/v1",
        )

    return OpenAI()


def _require_groq_api_key() -> str:
    import os

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY 환경변수가 필요합니다.")
    return api_key


def _create_structured_response(client, model: str, input_messages: list, schema_name: str, schema: Dict[str, Any]):
    """
    우선 json_schema를 사용하고, provider/모델이 미지원이면 json_object로 재시도한다.
    - Groq 일부 모델은 json_schema 미지원.
    """
    from openai import BadRequestError

    try:
        return client.responses.create(
            model=model,
            input=input_messages,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
    except BadRequestError as exc:
        message = str(exc)
        if "json_schema" not in message and "response_format" not in message:
            raise

        fallback_messages = list(input_messages)
        fallback_messages.append(
            {
                "role": "developer",
                "content": "반드시 JSON 객체만 출력하라. 설명 문장이나 코드블록을 출력하지 마라.",
            }
        )

        return client.responses.create(
            model=model,
            input=fallback_messages,
            text={"format": {"type": "json_object"}},
        )



def _gemini_generate_json(model: str, system_prompt: str, user_prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
    api_key = _require_gemini_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
    }

    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 429 or "RESOURCE_EXHAUSTED" in body or "quota" in body.lower():
            raise ApiQuotaExceededError("Gemini API quota exhausted") from exc
        raise RuntimeError(f"Gemini API 호출 실패: HTTP {exc.code} / {body}") from exc

    data = json.loads(raw)
    text = ""

    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            text = parts[0].get("text", "")

    if not text:
        raise RuntimeError(f"Gemini 응답에서 텍스트를 찾지 못했습니다: {data}")

    return json.loads(text)


def _require_gemini_api_key() -> str:
    import os

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")
    return api_key
