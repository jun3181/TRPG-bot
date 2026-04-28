import json
import os
import sys
from urllib import error, request

from config import (
    API_PROVIDER,
    EPISODES,
    EPSILON_END,
    EPSILON_START,
    GEMINI_MODEL,
    LEARNING_RATE,
    MODEL,
)
from experiment import train


def print_openai_install_guide():
    print("[안내] openai 파이썬 패키지가 설치되어 있지 않습니다.")
    print("[안내] 아래 명령어로 설치 후 다시 실행하세요.")
    print(f"  {sys.executable} -m pip install openai")
    print("  또는")
    print(f"  {sys.executable} -m pip install -r requirements.txt")


def _build_openai_compatible_client():
    from openai import OpenAI

    if API_PROVIDER == "groq":
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GROQ_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
    return OpenAI(api_key=api_key)


def check_gpt_connection() -> bool:
    if API_PROVIDER == "gemini":
        return check_gemini_connection()

    try:
        client = _build_openai_compatible_client()
        response = client.responses.create(
            model=MODEL,
            input=[{"role": "user", "content": "연결 테스트: OK만 답해줘."}],
            max_output_tokens=20,
        )
        preview = (response.output_text or "").strip()
        print(f"[GPT 연결 성공] provider={API_PROVIDER}, model={MODEL}, 응답={preview}")
        return True
    except ModuleNotFoundError as exc:
        if exc.name == "openai":
            print("[GPT 연결 실패] No module named 'openai'")
            print_openai_install_guide()
            return False
        print(f"[GPT 연결 실패] {exc}")
        return False
    except Exception as exc:
        print(f"[GPT 연결 실패] {exc}")
        return False


def check_gemini_connection() -> bool:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[Gemini 연결 실패] GEMINI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "연결 테스트: OK"}]}],
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
        print(f"[Gemini 연결 성공] model={GEMINI_MODEL}, 응답길이={len(raw)}")
        return True
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"[Gemini 연결 실패] HTTP {exc.code}: {body}")
        return False
    except Exception as exc:
        print(f"[Gemini 연결 실패] {exc}")
        return False


def chat_once(user_text: str) -> str:
    if API_PROVIDER == "gemini":
        return _gemini_chat_once(user_text)
    return _openai_compatible_chat_once(user_text)


def _openai_compatible_chat_once(user_text: str) -> str:
    client = _build_openai_compatible_client()
    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": "너는 TRPG 시스템 연결 점검용 챗봇이다. 한국어로 짧고 명확하게 대답한다.",
            },
            {"role": "user", "content": user_text},
        ],
        max_output_tokens=200,
    )
    return (response.output_text or "").strip()


def _gemini_chat_once(user_text: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": "너는 TRPG 시스템 연결 점검용 챗봇이다. 한국어로 짧고 명확하게 대답한다."}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
    }
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini 응답이 비어 있습니다: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError(f"Gemini 응답 텍스트를 찾지 못했습니다: {data}")

    return (parts[0].get("text", "") or "").strip()


def ask_int(prompt: str, default: int, minimum: int = 1) -> int:
    raw = input(f"{prompt} (기본값: {default}): ").strip()
    if not raw:
        return default

    try:
        value = int(raw)
    except ValueError:
        print(f"숫자만 입력 가능합니다. 기본값 {default}를 사용합니다.")
        return default

    if value < minimum:
        print(f"{minimum} 이상만 가능합니다. 기본값 {default}를 사용합니다.")
        return default

    return value


def ask_float(prompt: str, default: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    raw = input(f"{prompt} (기본값: {default}): ").strip()
    if not raw:
        return default

    try:
        value = float(raw)
    except ValueError:
        print(f"숫자만 입력 가능합니다. 기본값 {default}를 사용합니다.")
        return default

    if not (minimum <= value <= maximum):
        print(f"{minimum} ~ {maximum} 범위만 가능합니다. 기본값 {default}를 사용합니다.")
        return default

    return value


def ask_training_config():
    print("\n학습 설정을 입력하세요. (엔터 입력 시 기본값 사용)")
    epochs = ask_int("에포크 수", default=1, minimum=1)
    episodes_per_epoch = ask_int("에포크당 에피소드 수", default=EPISODES, minimum=1)
    learning_rate = ask_float("학습률(learning rate)", default=LEARNING_RATE, minimum=0.000001, maximum=1.0)
    epsilon_start = ask_float("탐험률 시작값(epsilon start)", default=EPSILON_START, minimum=0.0, maximum=1.0)
    epsilon_end = ask_float("탐험률 종료값(epsilon end)", default=EPSILON_END, minimum=0.0, maximum=1.0)
    log_every = ask_int("진행 로그 출력 주기(episode)", default=100, minimum=1)

    if epsilon_end > epsilon_start:
        print("epsilon end가 start보다 커서 값을 교체합니다.")
        epsilon_start, epsilon_end = epsilon_end, epsilon_start

    total_episodes = epochs * episodes_per_epoch

    print("\n설정 요약")
    print(f"- epochs: {epochs}")
    print(f"- episodes_per_epoch: {episodes_per_epoch}")
    print(f"- total_episodes: {total_episodes}")
    print(f"- learning_rate: {learning_rate}")
    print(f"- epsilon_start: {epsilon_start}")
    print(f"- epsilon_end: {epsilon_end}")
    print(f"- log_every: {log_every}")

    return total_episodes, learning_rate, epsilon_start, epsilon_end, log_every


def main():
    print("=== TRPG RL experiment_test ===")
    print(f"API_PROVIDER = {API_PROVIDER}, MODEL = {MODEL}")
    connected = check_gpt_connection()

    if not connected:
        print("GPT 연결이 확인되지 않아 종료합니다.")
        return

    print("\n이제 챗봇과 직접 대화해 API 적용 여부를 확인하세요.")
    print("- 일반 문장: 챗봇에게 전달")
    print("- !test_start: 강화학습 설정 입력 후 학습 시작")
    print("- !exit: 종료")

    while True:
        user_text = input("당신> ").strip()

        if not user_text:
            continue

        if user_text == "!exit":
            print("종료합니다.")
            return

        if user_text == "!test_start":
            total_episodes, learning_rate, epsilon_start, epsilon_end, log_every = ask_training_config()
            print(f"\n학습 시작 (OpenAI 호환 API 사용: True)")
            policy, logs = train(
                use_openai_for_training=True,
                episodes=total_episodes,
                learning_rate=learning_rate,
                epsilon_start=epsilon_start,
                epsilon_end=epsilon_end,
                log_every=log_every,
            )

            print("\n학습 완료")
            print(f"총 에피소드: {len(logs)}")
            print("최종 Q-values:")
            for action, q in sorted(policy.q_values.items(), key=lambda x: x[1], reverse=True):
                print(f"  {action}: {q:.3f}")
            return

        try:
            answer = chat_once(user_text)
            print(f"챗봇> {answer}")
        except Exception as exc:
            print(f"[대화 실패] {exc}")


if __name__ == "__main__":
    main()
