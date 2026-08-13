import json
import logging
import os
import secrets
from typing import Any

import uvicorn
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from repositories.review_repository import ReviewRepository
from services.review_service import ReviewService
from tools.aggregation import register_aggregation_tool
from tools.latest import register_latest_tool
from tools.search import register_search_tool

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("ybigta-mcp")


class StaticBearerAuthMiddleware:
    """MCP/호환 API 요청에 정적 Bearer Token 인증을 적용한다."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        if not token:
            raise RuntimeError("MCP_AUTH_TOKEN 환경변수가 필요합니다.")
        self.app = app
        self.expected = f"Bearer {token}".encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # lifespan/websocket은 그대로 전달한다.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 헬스체크는 인증 없이 허용한다.
        if scope.get("path") == "/health":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"")

        if not secrets.compare_digest(authorization, self.expected):
            body = b'{"error":"unauthorized"}'
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)


def _parse_allowed_hosts() -> list[str]:
    raw = os.environ.get(
        "MCP_ALLOWED_HOSTS",
        "localhost,localhost:8000,127.0.0.1,127.0.0.1:8000",
    )
    return [item.strip() for item in raw.split(",") if item.strip()]


repository = ReviewRepository()
service = ReviewService(repository)

mcp = MCPServer(
    "YBIGTA Kakao Review MCP",
    version="1.0.0",
    instructions=(
        "카카오맵 경복궁 리뷰를 안전하게 조회하는 read-only MCP 서버입니다. "
        "Raw SQL은 제공하지 않으며 조회 범위가 제한된 Tool만 제공합니다."
    ),
)

register_latest_tool(mcp, service)
register_search_tool(mcp, service)
register_aggregation_tool(mcp, service)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok", "service": "ybigta-review-mcp"})


# -----------------------------------------------------------------------------
# 기존 web/app/api/chat/route.ts 와 바로 연결하기 위한 호환 HTTP endpoint.
# 표준 MCP endpoint는 /mcp 이며, Inspector에서는 반드시 /mcp 를 사용한다.
# -----------------------------------------------------------------------------
async def _body(request: Request) -> dict[str, Any]:
    try:
        value = await request.json()
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, ValueError):
        return JSONResponse({"error": str(exc)}, status_code=400)
    logger.exception("Unhandled API error")
    return JSONResponse({"error": "internal_server_error"}, status_code=500)


@mcp.custom_route("/tools/get_latest_reviews", methods=["POST"])
async def latest_compat(request: Request) -> Response:
    try:
        data = await _body(request)
        return JSONResponse(service.get_latest_reviews(data.get("limit", 5)))
    except Exception as exc:
        return _error_response(exc)


@mcp.custom_route("/tools/search_reviews", methods=["POST"])
async def search_compat(request: Request) -> Response:
    try:
        data = await _body(request)
        return JSONResponse(
            service.search_reviews(
                keyword=data.get("keyword", ""),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                limit=data.get("limit", 5),
            )
        )
    except Exception as exc:
        return _error_response(exc)


@mcp.custom_route("/tools/aggregate_ratings", methods=["POST"])
async def aggregate_compat(request: Request) -> Response:
    try:
        data = await _body(request)
        return JSONResponse(
            service.aggregate_ratings(
                start_date=data.get("start_date", ""),
                end_date=data.get("end_date", ""),
            )
        )
    except Exception as exc:
        return _error_response(exc)


security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=_parse_allowed_hosts(),
    # Next.js/Vercel은 server-to-server 호출이므로 일반적으로 Origin 헤더가 없다.
    allowed_origins=[],
)

_mcp_app = mcp.streamable_http_app(transport_security=security)
app = StaticBearerAuthMiddleware(_mcp_app, os.environ.get("MCP_AUTH_TOKEN", ""))


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=os.environ.get("MCP_BIND_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_PORT", "8000")),
        reload=False,
    )
