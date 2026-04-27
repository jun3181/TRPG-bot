import os
import sys
import json
from typing import Tuple
from urllib import error, request

from config import API_PROVIDER, GEMINI_MODEL, MODEL
from experiment import train


def print_openai_install_guide():
    print("[안내] openai 파이썬 패키지가 설치되어 있지 않습니다.")
    print("[안내] 아래 명령어로 설치 후 다시 실행하세요.")
    print(f"  {sys.executable} -m pip install openai")
    print("  또는")
    print(f"  {sys.executable} -m pip install -r requirements.txt")


def check_gpt_connection() -> Tuple[bool, str]:
    if API_PROVIDER == "gemini":
        return check_gemini_connection()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("[GPT 연결 실패] OPENAI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
        return False, "missing_api_key"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=MODEL,
            input=[{"role": "user", "content": "연결 테스트: OK만 답해줘."}],
            max_output_tokens=20,
        )
        preview = (response.output_text or "").strip()
        print(f"[GPT 연결 성공] model={MODEL}, 응답={preview}")
        return True, "ok"
    except ModuleNotFoundError as exc:
        if exc.name == "openai":
            print("[GPT 연결 실패] No module named 'openai'")
            print_openai_install_guide()
            return False, "missing_openai_package"
        print(f"[GPT 연결 실패] {exc}")
        return False, "module_error"
    except Exception as exc:
        err_text = str(exc)
        if "insufficient_quota" in err_text or "Error code: 429" in err_text:
            print("[GPT 연결 실패] 현재 OpenAI API 사용량/크레딧 한도를 초과했습니다 (429 insufficient_quota).")
            print("[안내] platform.openai.com의 Billing/Usage에서 결제수단, 한도, 크레딧 상태를 확인하세요.")
            print("[안내] 지금은 Mock 모드로 학습을 진행할 수 있습니다.")
            return False, "insufficient_quota"
        print(f"[GPT 연결 실패] {exc}")
        return False, "other_error"


def check_gemini_connection() -> Tuple[bool, str]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[Gemini 연결 실패] GEMINI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
        return False, "missing_api_key"

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
        return True, "ok"
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 429 or "RESOURCE_EXHAUSTED" in body or "quota" in body.lower():
            print("[Gemini 연결 실패] 429 RESOURCE_EXHAUSTED / quota 초과")
            return False, "insufficient_quota"
        print(f"[Gemini 연결 실패] HTTP {exc.code}: {body}")
        return False, "other_error"
    except Exception as exc:
        print(f"[Gemini 연결 실패] {exc}")
        return False, "other_error"


def main():
    print("=== TRPG RL experiment_test ===")
    print(f"API_PROVIDER = {API_PROVIDER}, MODEL = {MODEL}")
    connected, reason = check_gpt_connection()

    print("\n명령어를 입력하세요.")
    print("- !test_start : 학습 시작")
    command = input("> ").strip()

    if command != "!test_start":
        print("지원하지 않는 명령어입니다. !test_start 만 지원합니다.")
        return

    if connected:
        use_openai_for_training = True
    else:
        use_openai_for_training = False
        print(f"API 연결 실패 사유: {reason}. Mock 모드로 진행합니다.")

    print(f"학습 시작 (OpenAI 사용: {use_openai_for_training})")

    policy, logs = train(use_openai_for_training=use_openai_for_training)

    print("\n학습 완료")
    print(f"총 에피소드: {len(logs)}")
    print("최종 Q-values:")
    for action, q in sorted(policy.q_values.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action}: {q:.3f}")


if __name__ == "__main__":
    main()
