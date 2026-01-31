```
[User Input]
     ↓
[LLM (GPT)]
- 광고 문구
- 배경 프롬프트
- 레이아웃 JSON
     ↓
[BiRefNet]
- 제품 배경 제거 (RGBA)
     ↓
[Flux.1 (+ LoRA)]
- 배경 생성
     ↓
[IC-Light]
- 조명/그림자 합성
     ↓
[Render Service]
- 문구, 위치, 폰트 합성
     ↓
[Real-ESRGAN]
- 업스케일 / 선명도
     ↓
[Output]
- 인스타 / 포스터 / 배너

```

| 요구 기술          | 실제 적용 위치       |
|-|-|
| **LoRA**       | Flux 배경 스타일 고정 |
| **DreamBooth** | 특정 브랜드/제품 학습   |
| **IP-Adapter** | 배경 스타일 참조 이미지  |
| **ControlNet** | 구도/조명/레이아웃 고정  |
| **LLM**        | 기획 + JSON 설계   |





```
ad_creator_platform/
│
├─ README.md
├─ requirements.txt
├─ .env.example
│
├─ app/                          # 🔹 공통 애플리케이션 레이어
│   ├─ main.py                   # Streamlit 엔트리 (로그인/라우팅)
│   │
│   ├─ core/                     # 공통 핵심 로직
│   │   ├─ config.py             # 환경설정
│   │   ├─ auth.py               # 이메일 로그인 / 세션
│   │   └─ logging.py            # 공통 로그
│   │
│   ├─ storage/                  # 저장소 추상화
│   │   ├─ local_fs.py           # 로컬 파일 저장 (현재)
│   │   └─ metadata.py           # 이력 JSON 관리
│   │
│   ├─ services/                 # 공통 서비스
│   │   ├─ copy_service.py       # 광고 문구 생성
│   │   ├─ image_service.py      # 이미지 생성 (HF/OpenAI)
│   │   ├─ render_service.py     # 레이어 합성 (bg/main/text)
│   │   └─ email_service.py      # 이메일 발송
│   │
│   └─ ui/                       # 공통 UI 컴포넌트
│       ├─ navbar.py
│       └─ guards.py             # 로그인/권한 가드
│
├─ modules/                      # 🔹 광고 타입별 모듈 (핵심)
│   ├─ instagram/                # ⭐ 인스타 광고 모듈
│   │   ├─ __init__.py
│   │   ├─ config.py             # 인스타 전용 설정
│   │   ├─ prompts/
│   │   │   └─ feed.yaml
│   │   ├─ pages/
│   │   │   ├─ generate.py       # 인스타 광고 생성
│   │   │   └─ history.py        # 인스타 광고 이력
│   │   └─ pipeline.py           # 인스타 전용 파이프라인
│   │
│   ├─ banner/                   # (미래) 배너 광고
│   │   └─ ...
│   │
│   └─ poster/                   # (미래) 포스터 광고
│       └─ ...
│
├─ assets/
│   ├─ fonts/
│   │   └─ NotoSansKR-Bold.ttf
│   └─ samples/
│
├─ outputs/
│   └─ users/                    # 사용자별 결과 (로컬)
│
└─ docs/
    ├─ architecture.md
    └─ decisions.md
```