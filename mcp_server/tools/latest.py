import logging

from services.review_service import ReviewService

logger = logging.getLogger(__name__)


def register_latest_tool(mcp, service: ReviewService) -> None:
    @mcp.tool()
    def get_latest_reviews(limit: int = 5) -> dict:
        """가장 최근 카카오맵 리뷰를 조회한다. limit은 1~20만 허용한다."""
        logger.info("MCP tool called: get_latest_reviews(limit=%s)", limit)
        return service.get_latest_reviews(limit)
