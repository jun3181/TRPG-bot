import hashlib
import hmac
import json
import os
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any




GAME_START_INTRO = (
    "📍 위치: 시작의 마을\n"
    "🧙 촌장 에단: \"오, 모험가여! 시작의 마을에 온 걸 환영하네.\"\n"
    "🧙 촌장 에단: \"먼저 나와 대화해 나무검을 챙기고, 사슴 5마리 토벌 퀘스트를 받아가게!\"\n"
    "\n[시작 퀘스트 플로우]\n"
    "1) !대화하기 \"촌장 에단\"  (나무검 획득 + 퀘스트 수락)\n"
    "2) !필드  (사슴 5마리 처치)\n"
    "3) !마을탐방  (NPC 목록 확인)\n"
    "4) !대화하기 \"npc이름\"  (퀘스트 완료 보고)\n"
    "   - 예시: !대화하기 \"촌장 에단\""
)


class PlayerDesignManager:
    JOB_BONUSES = {
        "전사": {"speed": 0, "attack": 1, "defense": 2},
        "궁수": {"speed": 1, "attack": 2, "defense": 0},
        "힐러": {"speed": 1, "attack": 0, "defense": 1},
        "도적": {"speed": 2, "attack": 1, "defense": 0},
    }

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.auth_dir = self.base_dir / "auth"
        self.players_dir = self.base_dir / "players"
        self.setup_dir = self.base_dir / "setup"

        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.players_dir.mkdir(parents=True, exist_ok=True)
        self.setup_dir.mkdir(parents=True, exist_ok=True)

        self.logged_in_users: set[int] = set()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_json(self, file_path: Path) -> dict[str, Any] | None:
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save_json(self, file_path: Path, payload: dict[str, Any]) -> None:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _auth_file(self, user_id: int) -> Path:
        return self.auth_dir / f"{user_id}.json"

    def _player_file(self, user_id: int) -> Path:
        return self.players_dir / f"{user_id}.json"

    def _setup_file(self, user_id: int) -> Path:
        return self.setup_dir / f"{user_id}.json"

    def _hash_password(self, password: str, salt_hex: str | None = None) -> tuple[str, str]:
        salt_hex = salt_hex or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            120_000,
        )
        return salt_hex, digest.hex()

    def _roll_stats(self) -> dict[str, int]:
        return {
            "speed": random.randint(1, 6),
            "attack": random.randint(1, 6),
            "defense": random.randint(1, 6),
        }

    def _load_setup(self, user_id: int) -> dict[str, Any]:
        setup_file = self._setup_file(user_id)
        payload = self._load_json(setup_file)
        if payload:
            return payload

        payload = {
            "discord_user_id": user_id,
            "login_id": None,
            "password_set": False,
            "nickname": None,
            "job": None,
            "dice": None,
            "updated_at": self._now(),
        }
        self._save_json(setup_file, payload)
        return payload

    def _save_setup(self, user_id: int, payload: dict[str, Any]) -> None:
        payload["updated_at"] = self._now()
        self._save_json(self._setup_file(user_id), payload)

    # 1) !아이디
    def set_login_id(self, user_id: int, login_id: str) -> tuple[bool, str]:
        if not login_id or len(login_id.strip()) < 3:
            return False, "아이디는 3자 이상으로 입력해주세요."

        if self._auth_file(user_id).exists():
            return False, "이미 계정이 생성되어 있습니다. `!로그인 <아이디> <비번>`을 사용하세요."

        setup = self._load_setup(user_id)
        setup["login_id"] = login_id.strip()
        self._save_setup(user_id, setup)
        return True, f"아이디가 설정되었습니다: {setup['login_id']}\n다음 단계: `!비번 <비밀번호>`"

    # 1) !비번
    def set_password(self, user_id: int, password: str) -> tuple[bool, str]:
        if len(password) < 4:
            return False, "비밀번호는 4자 이상이어야 합니다."

        if self._auth_file(user_id).exists():
            return False, "이미 계정이 생성되어 있습니다. `!로그인 <아이디> <비번>`을 사용하세요."

        setup = self._load_setup(user_id)
        if not setup.get("login_id"):
            return False, "먼저 `!아이디 <아이디>`를 설정해주세요."

        salt, password_hash = self._hash_password(password)
        auth_payload = {
            "discord_user_id": user_id,
            "login_id": setup["login_id"],
            "salt": salt,
            "password_hash": password_hash,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self._save_json(self._auth_file(user_id), auth_payload)

        setup["password_set"] = True
        self._save_setup(user_id, setup)
        return True, "비밀번호가 설정되었고 계정 생성이 완료되었습니다.\n다음 단계: `!로그인 <아이디> <비밀번호>`"

    def login(self, user_id: int, login_id: str, password: str) -> tuple[bool, str]:
        auth = self._load_json(self._auth_file(user_id))
        if not auth:
            return False, "계정이 없습니다. `!아이디`와 `!비번`을 먼저 설정하세요."

        if auth.get("login_id") != login_id:
            return False, "아이디가 일치하지 않습니다."

        _, password_hash = self._hash_password(password, salt_hex=auth["salt"])
        if not hmac.compare_digest(password_hash, auth["password_hash"]):
            return False, "비밀번호가 올바르지 않습니다."

        self.logged_in_users.add(user_id)

        if self._player_file(user_id).exists():
            return True, "로그인 성공! 기존 플레이어 확인 완료. 게임 시작됩니다!\n" + GAME_START_INTRO

        return True, "로그인 성공!\n다음 단계: `!닉네임 <닉네임>`"

    def is_logged_in(self, user_id: int) -> bool:
        return user_id in self.logged_in_users

    def is_first_user(self, user_id: int) -> bool:
        return not self._auth_file(user_id).exists()

    def start_message(self, user_id: int) -> tuple[bool, str]:
        if self.is_first_user(user_id):
            return (
                True,
                "처음 오신 플레이어네요! 1단계부터 시작하세요:\n"
                "1) !아이디 <아이디>\n"
                "2) !비번 <비밀번호>\n"
                "3) !로그인 <아이디> <비밀번호>",
            )

        return (
            False,
            "기존 플레이어입니다. 로그인하세요! !아이디 / 비밀번호\n(실행: !로그인 <아이디> <비밀번호>)",
        )

    # 2) !닉네임
    def set_nickname(self, user_id: int, nickname: str) -> tuple[bool, str]:
        if not self.is_logged_in(user_id):
            return False, "먼저 `!로그인 <아이디> <비번>`을 해주세요."

        if len(nickname.strip()) < 2:
            return False, "닉네임은 2자 이상이어야 합니다."

        setup = self._load_setup(user_id)
        setup["nickname"] = nickname.strip()
        self._save_setup(user_id, setup)
        return True, f"닉네임이 설정되었습니다: {setup['nickname']}\n다음 단계: `!직업설정 <전사|궁수|힐러|도적>`"

    # 3) !직업설정
    def set_job(self, user_id: int, job: str) -> tuple[bool, str]:
        if not self.is_logged_in(user_id):
            return False, "먼저 `!로그인 <아이디> <비번>`을 해주세요."

        normalized_job = job.strip()
        if normalized_job not in self.JOB_BONUSES:
            return False, "직업은 전사/궁수/힐러/도적 중 하나여야 합니다."

        setup = self._load_setup(user_id)
        setup["job"] = normalized_job
        self._save_setup(user_id, setup)
        return True, f"직업이 설정되었습니다: {normalized_job}\n다음 단계: `!주사위 던지기`"

    # 4) !주사위 던지기
    def roll_dice(self, user_id: int) -> tuple[bool, str, dict[str, Any] | None]:
        if not self.is_logged_in(user_id):
            return False, "먼저 `!로그인 <아이디> <비번>`을 해주세요.", None

        setup = self._load_setup(user_id)
        if not setup.get("nickname"):
            return False, "먼저 `!닉네임 <닉네임>`을 설정해주세요.", None
        if not setup.get("job"):
            return False, "먼저 `!직업설정 <직업>`을 설정해주세요.", None

        base_stats = self._roll_stats()
        setup["dice"] = base_stats
        self._save_setup(user_id, setup)
        return True, "주사위를 굴렸습니다.\n다음 단계: `!캐릭터생성` 또는 `!캐릭터 생성`", base_stats

    # 마지막 !캐릭터 생성
    def finalize_character(self, user_id: int) -> tuple[bool, str, dict[str, Any] | None]:
        if not self.is_logged_in(user_id):
            return False, "먼저 `!로그인 <아이디> <비번>`을 해주세요.", None

        if self._player_file(user_id).exists():
            return False, "이미 생성된 캐릭터가 있습니다.", None

        setup = self._load_setup(user_id)
        if not setup.get("nickname"):
            return False, "`!닉네임 <닉네임>` 단계가 필요합니다.", None
        if not setup.get("job"):
            return False, "`!직업설정 <직업>` 단계가 필요합니다.", None
        if not setup.get("dice"):
            return False, "`!주사위 던지기` 단계가 필요합니다.", None

        base_stats = setup["dice"]
        bonus_stats = self.JOB_BONUSES[setup["job"]]
        final_stats = {k: base_stats[k] + bonus_stats[k] for k in base_stats.keys()}

        now = self._now()
        player_payload = {
            "player_id": user_id,
            "login_id": setup.get("login_id"),
            "nickname": setup["nickname"],
            "job": setup["job"],
            "stats": {
                "base": base_stats,
                "bonus": bonus_stats,
                "final": final_stats,
            },
            "created_at": now,
            "updated_at": now,
        }
        self._save_json(self._player_file(user_id), player_payload)
        return True, "캐릭터 생성이 완료되었습니다! TRPG 준비 완료입니다.\n" + GAME_START_INTRO, player_payload

    def get_character(self, user_id: int) -> tuple[bool, str, dict[str, Any] | None]:
        payload = self._load_json(self._player_file(user_id))
        if not payload:
            return False, "생성된 캐릭터가 없습니다.", None
        return True, "조회 성공", payload


DEFAULT_DATA_ROOT = Path(os.getenv("PLAYER_DATA_ROOT", Path(__file__).resolve().parent / "playerdata"))
player_design_manager = PlayerDesignManager(DEFAULT_DATA_ROOT)
