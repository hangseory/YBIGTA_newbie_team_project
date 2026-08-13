import logging

from services.review_service import ReviewService

logger = logging.getLogger(__name__)


def register_aggregation_tool(mcp, service: ReviewService) -> None:
    @mcp.tool()
    def aggregate_ratings(start_date: str, end_date: str) -> dict:
        """기간 내 평균 별점, 리뷰 수, 최소/최대 별점, 별점 분포를 집계한다."""
        logger.info(
            "MCP tool called: aggregate_ratings(start_date=%s, end_date=%s)",
            start_date,
            end_date,
        )
        return service.aggregate_ratings(start_date, end_date)
