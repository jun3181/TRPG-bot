import os

from config import MODEL, USE_OPENAI_FOR_TRAINING
from experiment import train


def check_gpt_connection() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("[GPT 연결 실패] OPENAI_API_KEY 환경변수가 비어 있습니다. (.env 또는 시스템 환경변수 확인)")
        return False

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
        return True
    except Exception as exc:
        print(f"[GPT 연결 실패] {exc}")
        return False


def main():
    print("=== TRPG RL experiment_test ===")
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
