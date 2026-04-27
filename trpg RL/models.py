from dataclasses import dataclass


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
