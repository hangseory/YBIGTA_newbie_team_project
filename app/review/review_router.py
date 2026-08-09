import os
import tempfile

import pandas as pd
from fastapi import APIRouter, HTTPException

from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.kakao_processor import KakaoMapProcessor
from review_analysis.preprocessing.googlemaps_processor import GoogleMapsProcessor
from review_analysis.preprocessing.tripadvisor_processor import TripAdvisorProcessor


router = APIRouter(
    prefix="/review",
    tags=["review"]
)


# API에서 받을 이름 -> 실제 MongoDB collection 이름
COLLECTION_MAP = {
    "kakao": "reviews_kakao",
    "google": "reviews_GoogleMaps",
    "tripadvisor": "reviews_트립어드바이저",
}


# API에서 받을 이름 -> 사용할 전처리 클래스
PROCESSOR_MAP = {
    "kakao": KakaoMapProcessor,
    "google": GoogleMapsProcessor,
    "tripadvisor": TripAdvisorProcessor,
}


@router.post("/preprocess/{site_name}")
def preprocess_review(site_name: str):

    site_name = site_name.lower()

    # 1. 지원하는 사이트인지 확인
    if site_name not in COLLECTION_MAP:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 site_name입니다."
        )

    # 2. MongoDB 원본 collection 선택
    raw_collection_name = COLLECTION_MAP[site_name]
    raw_collection = mongo_db[raw_collection_name]

    # _id는 필요 없으므로 제외
    raw_data = list(
        raw_collection.find({}, {"_id": 0})
    )

    if not raw_data:
        raise HTTPException(
            status_code=404,
            detail="전처리할 데이터가 없습니다."
        )

    # 3. MongoDB 데이터 -> DataFrame
    df = pd.DataFrame(raw_data)

    # 기존 processor는 review 컬럼을 사용하므로 맞춰줌
    if "content" in df.columns and "review" not in df.columns:
        df = df.rename(columns={"content": "review"})

    # 4. 임시 폴더/CSV 생성
    with tempfile.TemporaryDirectory() as temp_dir:

        input_file = os.path.join(temp_dir, "input.csv")

        df.to_csv(
            input_file,
            index=False,
            encoding="utf-8-sig"
        )

        # 5. 기존 전처리 클래스 선택
        processor_class = PROCESSOR_MAP[site_name]

        processor = processor_class(
            input_path=input_file,
            output_dir=temp_dir
        )

        # 기존 preprocessing 코드 그대로 사용
        processor.preprocess()
        processor.feature_engineering()

        # 6. 전처리된 DataFrame
        processed_df = processor.df

    # NaN -> None
    processed_df = processed_df.where(
        pd.notna(processed_df),
        None
    )

    processed_data = processed_df.to_dict(
        orient="records"
    )

    # 7. 결과 저장할 collection
    processed_collection_name = f"processed_reviews_{site_name}"

    processed_collection = mongo_db[
        processed_collection_name
    ]

    # 기존 전처리 결과가 있으면 삭제
    processed_collection.delete_many({})

    # 새 결과 저장
    if processed_data:
        processed_collection.insert_many(
            processed_data
        )

    return {
        "site_name": site_name,
        "source_collection": raw_collection_name,
        "processed_collection": processed_collection_name,
        "before_count": len(raw_data),
        "after_count": len(processed_data)
    }