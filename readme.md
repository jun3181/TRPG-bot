# TRPG RL 실험 가이드

이 문서는 `trpg RL` 실험 코드를 실제로 실행하는 방법을 정리합니다.

## 1) 준비

### Python 패키지 설치

```bash
pip install openai
```

> `trpg RL/experiment_test.py`는 API 연결 확인을 먼저 수행합니다.

### 환경변수 설정

```bash
export OPENAI_API_KEY="<YOUR_API_KEY>"
```

선택적으로 아래 실험 파라미터를 바꿀 수 있습니다.

```bash
export OPENAI_MODEL="gpt-4.1-mini"
export TRPG_EPISODES="1000"
export TRPG_LEARNING_RATE="0.1"
export TRPG_EPSILON_START="0.30"
export TRPG_EPSILON_END="0.05"
export TRPG_USE_OPENAI_FOR_TRAINING="false"
export TRPG_USE_OPENAI_FOR_FINAL_TEST="false"
```

## 2) 빠른 실행 (권장)

루트에서 아래를 실행합니다.

```bash
python "trpg RL/experiment_test.py"
```

실행 흐름:

1. API 연결 확인 (`TRPG_API_PROVIDER` 기준)
2. 일반 문장을 입력해 챗봇과 직접 대화하며 연결 상태 확인
3. `!test_start` 입력
4. 에포크/에피소드/학습률/epsilon 등 설정값 입력
5. 학습 시작 후 결과 출력 및 로그 파일 생성

## 3) 기존 메인 스크립트 실행

아래 스크립트는 학습 후 최종 테스트(닉네임/입력)를 이어서 실행합니다.

```bash
python "trpg RL/trpg_prompt_rl_experiment.py"
```

## 4) 결과 파일

학습이 완료되면 아래 파일이 생성됩니다.

- `trpg RL/outputs/latest_prompt_pack.json`: 마지막 프롬프트 팩
- `trpg RL/outputs/prompt_packs.json`: 에피소드별 프롬프트 기록
- `trpg RL/outputs/episode_dialogues.csv`: 에피소드 대화 로그

## 5) 문제 해결

- `OPENAI_API_KEY`(또는 provider별 API key)가 비어 있으면 `trpg RL/experiment_test.py`는 학습을 시작하지 않습니다.
- OpenAI 패키지가 없으면 `pip install openai`로 설치하세요.
- API 호출 실패 시 키/모델/네트워크 상태를 확인하세요.
