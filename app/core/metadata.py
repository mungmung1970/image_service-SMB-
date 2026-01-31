# ad_creator_platform/app/core/metadata.py
"""
Ad Metadata Model

역할:
- 생성된 광고 결과의 메타데이터 구조 정의
- history.json 저장용 표준 포맷 제공
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


@dataclass
class AdMetadata:
    # 기본 식별 정보
    image_id: str
    ad_type: str
    user_email: str

    # 광고 정보
    product: str
    tone: str
    discount: Optional[str]

    # 프롬프트 정보
    prompt: str
    prompt_extra: Optional[str]

    # 이미지 정보
    image_provider: str
    image_path: str
    image_size: Tuple[int, int]

    # 생성 결과
    copy: Dict[str, str]

    # 시스템 메타
    created_at: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        history.json에 저장하기 위한 dict 변환
        """
        return asdict(self)
