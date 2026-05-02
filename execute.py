import os

from dotenv import load_dotenv
from openai import OpenAI

from text import run_bot

# .env 로드 (이미 설정된 값은 유지)
load_dotenv(override=False)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


def _create_llm_client() -> tuple[OpenAI, str]:
    provider = (_env("TRPG_API_PROVIDER", "groq") or "groq").lower()

    if provider == "groq":
        api_key = _env("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY가 비어 있습니다. .env를 확인하세요.")
        model = _env("GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        return client, model

    if provider == "openai":
        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 비어 있습니다. .env를 확인하세요.")
        model = _env("OPENAI_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini"
        client = OpenAI(api_key=api_key)
        return client, model

    raise RuntimeError("TRPG_API_PROVIDER는 groq 또는 openai 여야 합니다.")


def _chat_loop() -> None:
    client, model = _create_llm_client()

    print("\n=== API 연결 확인 채팅 모드 ===")
    print("- 질문을 입력하면 LLM 응답을 출력합니다.")
    print("- 연결이 확인되면 `!디스코드시작` 을 입력하세요.")
    print("- 종료: Ctrl+C 또는 !종료\n")

    messages = [
        {
            "role": "system",
            "content": "당신은 TRPG 준비를 도와주는 한국어 어시스턴트입니다. 간결하고 친절하게 답하세요.",
        }
    ]

    while True:
        user_text = input("You> ").strip()

        if not user_text:
            continue
        if user_text == "!종료":
            print("종료합니다.")
            return
        if user_text == "!디스코드시작":
            print("디스코드 봇을 시작합니다...\n")
            run_bot()
            return

        messages.append({"role": "user", "content": user_text})
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )
            answer = response.choices[0].message.content or "(빈 응답)"
        except Exception as exc:  # noqa: BLE001
            print(f"[API 오류] {exc}")
            continue

        print(f"Bot> {answer}\n")
        messages.append({"role": "assistant", "content": answer})


def main() -> None:
    _chat_loop()


if __name__ == "__main__":
    main()
