import logging

from services.review_service import ReviewService

logger = logging.getLogger(__name__)


def register_search_tool(mcp, service: ReviewService) -> None:
    @mcp.tool()
    def search_reviews(
        keyword: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 5,
    ) -> dict:
        """키워드가 포함된 리뷰를 검색한다. 날짜는 YYYY-MM-DD, limit은 최대 20이다."""
        logger.info(
            "MCP tool called: search_reviews(keyword=%r, start_date=%s, end_date=%s, limit=%s)",
            keyword,
            start_date,
            end_date,
            limit,
        )
        return service.search_reviews(keyword, start_date, end_date, limit)
