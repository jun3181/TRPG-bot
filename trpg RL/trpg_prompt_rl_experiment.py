from config import USE_OPENAI_FOR_FINAL_TEST, USE_OPENAI_FOR_TRAINING
from experiment import train
from generators import DialogueGenerator, PromptGenerator
from io_utils import save_prompt_json
from models import DialogueState
from reward import calculate_reward


def final_test(policy):
    print("\n==============================")
    print("최종 테스트")
    print("==============================")

    nickname = input("닉네임을 입력하세요: ").strip() or "플레이어"
    player_input = input("플레이어 입력: ").strip() or "네, 알겠습니다."

    state = DialogueState(
        scene_id="start_village",
        npc_id="village_chief",
        player_nickname=nickname,
        dialogue_step="player_reply_after_intro",
        line_count=2,
        max_line_count=5,
        weapon_given=False,
        quest_offered=False,
        player_input=player_input,
    )

    best_action = max(policy.q_values, key=policy.q_values.get)
    prompt_generator = PromptGenerator(use_openai=USE_OPENAI_FOR_FINAL_TEST)
    dialogue_generator = DialogueGenerator(use_openai=USE_OPENAI_FOR_FINAL_TEST)

    prompt_pack = prompt_generator.generate(state, best_action)
    result = dialogue_generator.generate(state, best_action, prompt_pack)
    save_prompt_json(prompt_pack)

    print(f"\n[선택된 Prompt Action: {best_action}]")
    for line in result["chief_lines"]:
        print(f"촌장: {line}")
    for line in result["system_lines"]:
        print(f"시스템: {line}")

    reward = calculate_reward(state, result)
    print(f"[보상 점수: {reward:.3f}]")


def main():
    print("TRPG Prompt RL 실험 시작")
    print(f"USE_OPENAI_FOR_TRAINING = {USE_OPENAI_FOR_TRAINING}")
    print(f"USE_OPENAI_FOR_FINAL_TEST = {USE_OPENAI_FOR_FINAL_TEST}")

    trained_policy, _training_logs = train(use_openai_for_training=USE_OPENAI_FOR_TRAINING)

    print("\n학습 완료")
    print("최종 Q-values:")
    for action, q in sorted(trained_policy.q_values.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action}: {q:.3f}")

    final_test(trained_policy)


if __name__ == "__main__":
    main()
