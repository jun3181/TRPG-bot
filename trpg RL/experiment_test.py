import json
import os
import sys
from urllib import error, request

from config import API_PROVIDER, GEMINI_MODEL, MODEL, USE_OPENAI_FOR_TRAINING
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


def main():
    print("=== TRPG RL experiment_test ===")
    print(f"API_PROVIDER = {API_PROVIDER}, MODEL = {MODEL}")
    connected = check_gpt_connection()

    print("\n명령어를 입력하세요.")
    print("- !test_start : 학습 시작")
    command = input("> ").strip()

    if command != "!test_start":
        print("지원하지 않는 명령어입니다. !test_start 만 지원합니다.")
        return

    if not connected:
        print("GPT 연결이 확인되지 않아 학습을 시작하지 않습니다.")
        return

    use_openai_for_training = True if connected else USE_OPENAI_FOR_TRAINING
    print(f"학습 시작 (OpenAI 사용: {use_openai_for_training})")

    policy, logs = train(use_openai_for_training=use_openai_for_training)

    print("\n학습 완료")
    print(f"총 에피소드: {len(logs)}")
    print("최종 Q-values:")
    for action, q in sorted(policy.q_values.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action}: {q:.3f}")


if __name__ == "__main__":
    main()
