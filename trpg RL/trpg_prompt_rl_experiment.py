# trpg_prompt_rl_experiment.py

import os
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

# 실제 OpenAI API를 쓸 때만 필요
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================
# 설정
# =========================

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

EPISODES = 1000
LEARNING_RATE = 0.1
EPSILON_START = 0.30
EPSILON_END = 0.05

# 기본은 비용 절약용 시뮬레이션.
# True로 바꾸면 1000번 학습 중에도 실제 OpenAI API를 호출함.
# 주의: Prompt Generator + Dialogue Generator라서 한 에피소드에 최대 2번 호출 가능.
USE_OPENAI_FOR_TRAINING = False

# 최종 테스트에서만 실제 OpenAI API 사용 여부
USE_OPENAI_FOR_FINAL_TEST = False


# =========================
# State
# =========================

@dataclass
class DialogueState:
    scene_id: str
    npc_id: str
    player_nickname: str
    dialogue_step: str
    line_count: int
    max_line_count: int
    weapon_given: bool
    quest_offered: bool
    player_input: str


# =========================
# Action
# 강화학습 모델이 고르는 것:
# "대사"가 아니라 "프롬프트 생성 전략"
# =========================

ACTIONS = {
    "fast_weapon_grant": {
        "description": "가장 빠르게 무기 지급까지 진행하는 프롬프트를 만들게 한다.",
        "target": "2문장 이내로 무기를 지급하고, 시스템 메시지에 '무기를 지급했습니다!'를 포함한다."
    },
    "friendly_tutorial": {
        "description": "친절하고 부드러운 튜토리얼 말투의 프롬프트를 만들게 한다.",
        "target": "플레이어 반응을 받아주되, 무기 지급을 자연스럽게 진행한다."
    },
    "immersive_intro": {
        "description": "세계관 몰입감을 살리는 프롬프트를 만들게 한다.",
        "target": "분위기를 살리지만 5줄 제한을 지킨다."
    },
    "adaptive_reply": {
        "description": "플레이어 입력을 강하게 반영하는 프롬프트를 만들게 한다.",
        "target": "플레이어 말에 반응하면서 무기 지급까지 진행한다."
    },
    "strict_goal": {
        "description": "목표 달성을 최우선으로 하는 강한 제약 프롬프트를 만들게 한다.",
        "target": "반드시 이번 응답에서 무기를 지급하고, '무기를 지급했습니다!'를 출력한다."
    }
}


# =========================
# Q-value Policy
# =========================

class PromptPolicy:
    def __init__(self, actions: Dict[str, Dict[str, str]]):
        self.q_values = {action_name: 0.5 for action_name in actions.keys()}

    def select_action(self, epsilon: float) -> str:
        if random.random() < epsilon:
            return random.choice(list(self.q_values.keys()))

        max_q = max(self.q_values.values())
        best_actions = [
            action for action, q in self.q_values.items()
            if q == max_q
        ]
        return random.choice(best_actions)

    def update(self, action: str, reward: float):
        old_q = self.q_values[action]
        self.q_values[action] = old_q + LEARNING_RATE * (reward - old_q)


# =========================
# 실험용 플레이어 입력
# =========================

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
    "알겠어요."
]


# =========================
# JSON Schema
# Dialogue Generator의 출력 고정
# =========================

DIALOGUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "chief_lines": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2
        },
        "system_lines": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 1
        },
        "state_update": {
            "type": "object",
            "properties": {
                "weapon_given": {"type": "boolean"},
                "dialogue_step": {"type": "string"},
                "line_count_add": {"type": "integer"}
            },
            "required": [
                "weapon_given",
                "dialogue_step",
                "line_count_add"
            ],
            "additionalProperties": False
        }
    },
    "required": [
        "chief_lines",
        "system_lines",
        "state_update"
    ],
    "additionalProperties": False
}


# =========================
# Prompt Generator
# 실제 API를 쓰는 버전
# =========================

def call_prompt_generator_api(state: DialogueState, action_name: str) -> Dict[str, str]:
    if OpenAI is None:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. pip install openai")

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
- 최종 출력 어딘가에 반드시 "무기를 지급했습니다!" 문장이 나오게 해야 한다.

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
- description: {action["description"]}
- target: {action["target"]}

Dialogue Generator에게 줄 프롬프트 3개를 작성하라:
1. system_prompt
2. developer_prompt
3. user_prompt

단, Dialogue Generator는 촌장 대사 1~2줄과 시스템 메시지 1줄만 생성해야 한다.
""".strip()

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
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
                        "user_prompt": {"type": "string"}
                    },
                    "required": [
                        "system_prompt",
                        "developer_prompt",
                        "user_prompt"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    return json.loads(response.output_text)


# =========================
# Prompt Generator
# 비용 절약용 Mock 버전
# =========================

def mock_prompt_generator(state: DialogueState, action_name: str) -> Dict[str, str]:
    action = ACTIONS[action_name]

    system_prompt = """
너는 한국어 TRPG 게임의 시작마을 촌장 NPC를 연기한다.
촌장은 친절한 튜토리얼 안내자다.
불필요한 세계관 설명을 하지 않는다.
출력은 반드시 JSON 형식으로 한다.
""".strip()

    developer_prompt = f"""
선택된 전략: {action_name}
전략 설명: {action["description"]}
전략 목표: {action["target"]}

제약:
- chief_lines는 1~2줄만 작성한다.
- system_lines는 정확히 1줄만 작성한다.
- system_lines에는 반드시 "무기를 지급했습니다!"를 포함한다.
- state_update.weapon_given은 반드시 true여야 한다.
- 전체 대화 흐름은 5줄 이내로 끝나야 한다.
""".strip()

    user_prompt = f"""
이미 출력된 촌장 대사:
1. 안녕하신가 {state.player_nickname}이여, 나는 시작의 마을의 촌장님일세.
2. 여기서 기본적인 튜토리얼을 배울 것일세.

플레이어 입력:
"{state.player_input}"

해야 할 일:
- 플레이어 입력에 짧게 반응한다.
- 촌장이 기본 무기를 지급한다.
- 시스템 메시지로 "{state.player_nickname}에게 무기를 지급했습니다!"를 출력한다.
""".strip()

    return {
        "system_prompt": system_prompt,
        "developer_prompt": developer_prompt,
        "user_prompt": user_prompt
    }


# =========================
# Dialogue Generator
# 실제 API 버전
# =========================

def call_dialogue_generator_api(prompt_pack: Dict[str, str]) -> Dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. pip install openai")

    client = OpenAI()

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": prompt_pack["system_prompt"]},
            {"role": "developer", "content": prompt_pack["developer_prompt"]},
            {"role": "user", "content": prompt_pack["user_prompt"]}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "chief_dialogue_result",
                "strict": True,
                "schema": DIALOGUE_OUTPUT_SCHEMA
            }
        }
    )

    return json.loads(response.output_text)


# =========================
# Dialogue Generator
# 비용 절약용 Mock 버전
# =========================

def mock_dialogue_generator(state: DialogueState, action_name: str) -> Dict[str, Any]:
    """
    실제 GPT 대신 간단한 규칙으로 결과를 만드는 함수.
    학습 구조가 돌아가는지 확인하는 용도.
    """

    if action_name == "fast_weapon_grant":
        chief_lines = [
            "좋은 자세일세. 모험의 첫걸음은 준비에서 시작되는 법이지.",
            "자, 이 기본 무기를 받게나."
        ]
    elif action_name == "friendly_tutorial":
        chief_lines = [
            "걱정 말게, 처음이라면 내가 차근차근 알려주겠네.",
            "우선 이 기본 무기를 받아 들게나."
        ]
    elif action_name == "immersive_intro":
        # 일부러 조금 장황해질 가능성이 있는 전략
        chief_lines = [
            "이 마을 밖 숲에는 작은 위험들이 숨어 있지만, 그것도 모험의 시작이라네.",
            "그러니 이 기본 무기를 받고 첫걸음을 내딛게나."
        ]
    elif action_name == "adaptive_reply":
        chief_lines = [
            f"'{state.player_input}'라, 좋은 대답일세.",
            "그럼 바로 이 기본 무기를 받게나."
        ]
    else:
        chief_lines = [
            "좋네. 지금 가장 중요한 건 준비를 마치는 것일세.",
            "이 기본 무기를 받고 바로 연습을 시작하게."
        ]

    system_lines = [
        f"{state.player_nickname}에게 무기를 지급했습니다!"
    ]

    return {
        "chief_lines": chief_lines,
        "system_lines": system_lines,
        "state_update": {
            "weapon_given": True,
            "dialogue_step": "weapon_given",
            "line_count_add": len(chief_lines) + len(system_lines)
        }
    }


# =========================
# Reward 계산
# =========================

def calculate_reward(state: DialogueState, result: Dict[str, Any]) -> float:
    chief_lines = result.get("chief_lines", [])
    system_lines = result.get("system_lines", [])
    state_update = result.get("state_update", {})

    weapon_given = bool(state_update.get("weapon_given", False))

    total_lines = state.line_count + len(chief_lines) + len(system_lines)
    line_limit_success = total_lines <= state.max_line_count

    system_text = " ".join(system_lines)
    required_sentence_success = "무기를 지급했습니다" in system_text

    chief_text = " ".join(chief_lines)
    has_weapon_word = "무기" in chief_text or "검" in chief_text

    # 보상 설계
    reward = 0.0

    # 가장 중요: 무기 지급 성공
    if weapon_given:
        reward += 0.45

    # 5줄 제한 성공
    if line_limit_success:
        reward += 0.25

    # 원하는 문장 포함
    if required_sentence_success:
        reward += 0.20

    # 촌장 대사에 무기 지급 맥락이 있음
    if has_weapon_word:
        reward += 0.10

    return min(reward, 1.0)


# =========================
# 한 에피소드 실행
# =========================

def run_episode(
    policy: PromptPolicy,
    episode_index: int,
    use_openai: bool = False
) -> Dict[str, Any]:
    epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * (1 - episode_index / EPISODES)

    player_input = random.choice(PLAYER_INPUT_SAMPLES)

    state = DialogueState(
        scene_id="start_village",
        npc_id="village_chief",
        player_nickname="플레이어",
        dialogue_step="player_reply_after_intro",
        line_count=2,
        max_line_count=5,
        weapon_given=False,
        quest_offered=False,
        player_input=player_input
    )

    action_name = policy.select_action(epsilon)

    if use_openai:
        prompt_pack = call_prompt_generator_api(state, action_name)
        result = call_dialogue_generator_api(prompt_pack)
    else:
        prompt_pack = mock_prompt_generator(state, action_name)
        result = mock_dialogue_generator(state, action_name)

    reward = calculate_reward(state, result)
    policy.update(action_name, reward)

    return {
        "episode": episode_index,
        "state": state,
        "action": action_name,
        "prompt_pack": prompt_pack,
        "result": result,
        "reward": reward
    }


# =========================
# 1000번 학습
# =========================

def train():
    policy = PromptPolicy(ACTIONS)

    logs = []

    for i in range(1, EPISODES + 1):
        log = run_episode(
            policy=policy,
            episode_index=i,
            use_openai=USE_OPENAI_FOR_TRAINING
        )
        logs.append(log)

        if i % 100 == 0:
            print(f"\n[{i} episode 완료]")
            print("현재 Q-values:")
            for action, q in sorted(policy.q_values.items(), key=lambda x: x[1], reverse=True):
                print(f"  {action}: {q:.3f}")

    return policy, logs


# =========================
# 학습된 모델로 실제 대화 테스트
# =========================

def final_test(policy: PromptPolicy):
    print("\n==============================")
    print("최종 테스트")
    print("==============================")

    nickname = input("닉네임을 입력하세요: ").strip() or "플레이어"

    print(f"\n촌장: 안녕하신가 {nickname}이여, 나는 시작의 마을의 촌장님일세.")
    print("촌장: 여기서 기본적인 튜토리얼을 배울 것일세.")

    player_input = input("\n플레이어: ").strip() or "네, 알겠습니다."

    state = DialogueState(
        scene_id="start_village",
        npc_id="village_chief",
        player_nickname=nickname,
        dialogue_step="player_reply_after_intro",
        line_count=2,
        max_line_count=5,
        weapon_given=False,
        quest_offered=False,
        player_input=player_input
    )

    # 최종 테스트에서는 탐험 없이 가장 Q값 높은 전략 선택
    best_action = max(policy.q_values, key=policy.q_values.get)

    print(f"\n[선택된 Prompt Action: {best_action}]")

    if USE_OPENAI_FOR_FINAL_TEST:
        prompt_pack = call_prompt_generator_api(state, best_action)
        result = call_dialogue_generator_api(prompt_pack)
    else:
        prompt_pack = mock_prompt_generator(state, best_action)
        result = mock_dialogue_generator(state, best_action)

    print("\n--- 촌장 응답 ---")
    for line in result["chief_lines"]:
        print(f"촌장: {line}")

    for line in result["system_lines"]:
        print(f"시스템: {line}")

    reward = calculate_reward(state, result)
    print(f"\n[보상 점수: {reward:.3f}]")

    if result["state_update"]["weapon_given"]:
        print("[상태 변경] weapon_given = True")


# =========================
# 실행
# =========================

if __name__ == "__main__":
    print("TRPG Prompt RL 실험 시작")
    print(f"EPISODES = {EPISODES}")
    print(f"USE_OPENAI_FOR_TRAINING = {USE_OPENAI_FOR_TRAINING}")
    print(f"USE_OPENAI_FOR_FINAL_TEST = {USE_OPENAI_FOR_FINAL_TEST}")

    trained_policy, training_logs = train()

    print("\n학습 완료")
    print("최종 Q-values:")
    for action, q in sorted(trained_policy.q_values.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action}: {q:.3f}")

    final_test(trained_policy)