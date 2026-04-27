import random
from typing import Any, Dict, List, Tuple

from config import ACTIONS, EPISODES, EPSILON_END, EPSILON_START, LEARNING_RATE, PLAYER_INPUT_SAMPLES
from generators import ApiQuotaExceededError, DialogueGenerator, PromptGenerator
from io_utils import export_episode_logs_csv, save_prompt_history_json, save_prompt_json
from models import DialogueState
from policy import PromptPolicy
from reward import calculate_reward


class TRPGRLExperiment:
    def __init__(self, use_openai_for_training: bool):
        self.policy = PromptPolicy(ACTIONS, learning_rate=LEARNING_RATE)
        self.prompt_generator = PromptGenerator(use_openai=use_openai_for_training)
        self.dialogue_generator = DialogueGenerator(use_openai=use_openai_for_training)

    def run_episode(self, episode_index: int) -> Dict[str, Any]:
        epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * (1 - episode_index / EPISODES)
        state = DialogueState(
            scene_id="start_village",
            npc_id="village_chief",
            player_nickname="플레이어",
            dialogue_step="player_reply_after_intro",
            line_count=2,
            max_line_count=5,
            weapon_given=False,
            quest_offered=False,
            player_input=random.choice(PLAYER_INPUT_SAMPLES),
        )

        action_name = self.policy.select_action(epsilon)
        prompt_pack = self.prompt_generator.generate(state, action_name)
        result = self.dialogue_generator.generate(state, action_name, prompt_pack)
        reward = calculate_reward(state, result)
        self.policy.update(action_name, reward)

        return {
            "episode": episode_index,
            "state": state,
            "action": action_name,
            "prompt_pack": prompt_pack,
            "result": result,
            "reward": reward,
        }


def train(use_openai_for_training: bool) -> Tuple[PromptPolicy, List[Dict[str, Any]]]:
    experiment = TRPGRLExperiment(use_openai_for_training=use_openai_for_training)
    logs: List[Dict[str, Any]] = []

    for i in range(1, EPISODES + 1):
        try:
            log = experiment.run_episode(i)
            logs.append(log)
            save_prompt_json(log["prompt_pack"])
        except ApiQuotaExceededError:
            print(f"\\n[{i} episode 중단] API 호출 한도(쿼터)가 소진되어 실험을 종료합니다.")
            break

        if i % 100 == 0:
            print(f"\\n[{i} episode 완료]")
            print("현재 Q-values:")
            for action, q in sorted(experiment.policy.q_values.items(), key=lambda x: x[1], reverse=True):
                print(f"  {action}: {q:.3f}")

    save_prompt_history_json(logs)
    export_episode_logs_csv(logs)
    return experiment.policy, logs
