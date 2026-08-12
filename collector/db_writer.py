import hashlib
import os
from datetime import datetime
from typing import List, TypedDict

import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv()


class ReviewRow(TypedDict):
    rating: int
    date: str
    review: str
    review_length: int


def _row_hash(rating: int, date: str, review: str) -> str:
    """rating + date + review 내용을 묶어 중복 판별용 해시를 만든다."""
    raw = f"{rating}|{date}|{review}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_reviews_from_csv(csv_path: str) -> List[ReviewRow]:
    """전처리된 카카오맵 리뷰 CSV를 읽어 DB에 넣을 행 목록으로 변환한다."""
    df = pd.read_csv(csv_path)

    rows: List[ReviewRow] = []
    for _, record in df.iterrows():
        rows.append(
            {
                "rating": int(record["rating"]),
                "date": str(record["date"]),
                "review": str(record["review"]),
                "review_length": int(record["review_length"]),
            }
        )
    return rows


def _get_connection() -> pymysql.connections.Connection:
    """collector 전용 DB 계정(collector_user)으로 RDS에 접속한다."""
    return pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["COLLECTOR_DB_USER"],
        password=os.environ["COLLECTOR_DB_PASSWORD"],
        database=os.environ["MYSQL_DB"],
        charset="utf8mb4",
        autocommit=False,
    )


def save_reviews(rows: List[ReviewRow]) -> int:
    """리뷰 목록을 RDS에 upsert한다.

    이미 존재하는 리뷰(review_hash가 같음)는 collected_at만 갱신하고,
    새로운 리뷰만 새 행으로 추가한다. 매 실행마다 대부분의 리뷰는
    이미 알고 있는 것이므로, 이렇게 해야 실행할 때마다 테이블이
    무한히 커지지 않는다.

    Returns:
        int: 이번 실행에서 처리(삽입 또는 갱신)된 행 수.
    """
    if not rows:
        return 0

    now = datetime.now()

    connection = _get_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO kakao_reviews
                    (rating, review_date, review, review_length,
                     review_hash, collected_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    collected_at = VALUES(collected_at)
            """
            params = [
                (
                    row["rating"],
                    row["date"],
                    row["review"],
                    row["review_length"],
                    _row_hash(row["rating"], row["date"], row["review"]),
                    now,
                )
                for row in rows
            ]
            cursor.executemany(sql, params)
        connection.commit()
        return len(rows)
    finally:
        connection.close()
