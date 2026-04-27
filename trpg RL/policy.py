import random
from typing import Dict


class PromptPolicy:
    def __init__(self, actions: Dict[str, Dict[str, str]], learning_rate: float):
        self.learning_rate = learning_rate
        self.q_values = {action_name: 0.5 for action_name in actions.keys()}

    def select_action(self, epsilon: float) -> str:
        if random.random() < epsilon:
            return random.choice(list(self.q_values.keys()))

        max_q = max(self.q_values.values())
        best_actions = [action for action, q in self.q_values.items() if q == max_q]
        return random.choice(best_actions)

    def update(self, action: str, reward: float):
        old_q = self.q_values[action]
        self.q_values[action] = old_q + self.learning_rate * (reward - old_q)
