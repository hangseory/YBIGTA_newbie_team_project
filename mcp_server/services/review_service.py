from datetime import date
from typing import Any

from repositories.review_repository import ReviewRepository


MAX_ROWS = 20
MAX_KEYWORD_LENGTH = 100


class ReviewService:
    """입력 검증/조회 범위 제한 후 Repository를 호출한다."""

    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_limit(limit: int | None, default: int = 5) -> int:
        if limit is None:
            return default
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("limit은 정수여야 합니다.")
        if not 1 <= limit <= MAX_ROWS:
            raise ValueError(f"limit은 1~{MAX_ROWS} 사이여야 합니다.")
        return limit

    @staticmethod
    def _validate_date(value: str | None, field_name: str) -> str | None:
        if value is None or value == "":
            return None
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name}는 YYYY-MM-DD 형식이어야 합니다.") from exc
        return value

    def get_latest_reviews(self, limit: int | None = 5) -> dict[str, Any]:
        safe_limit = self._validate_limit(limit)
        rows = self.repository.get_latest_reviews(safe_limit)
        return {"count": len(rows), "reviews": rows}

    def search_reviews(
        self,
        keyword: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = 5,
    ) -> dict[str, Any]:
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("keyword는 비어 있을 수 없습니다.")
        if len(keyword) > MAX_KEYWORD_LENGTH:
            raise ValueError(f"keyword는 {MAX_KEYWORD_LENGTH}자 이하여야 합니다.")

        start = self._validate_date(start_date, "start_date")
        end = self._validate_date(end_date, "end_date")
        if start and end and start > end:
            raise ValueError("start_date는 end_date보다 늦을 수 없습니다.")

        safe_limit = self._validate_limit(limit)
        rows = self.repository.search_reviews(keyword, start, end, safe_limit)
        return {
            "keyword": keyword,
            "start_date": start,
            "end_date": end,
            "count": len(rows),
            "reviews": rows,
        }

    def aggregate_ratings(self, start_date: str, end_date: str) -> dict[str, Any]:
        start = self._validate_date(start_date, "start_date")
        end = self._validate_date(end_date, "end_date")
        assert start is not None and end is not None
        if start > end:
            raise ValueError("start_date는 end_date보다 늦을 수 없습니다.")

        result = self.repository.aggregate_ratings(start, end)
        result.update({"start_date": start, "end_date": end})
        return result
