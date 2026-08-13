import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


class ReviewRepository:
    """RDS(MySQL)의 kakao_reviews를 read-only로 조회한다."""

    def __init__(self) -> None:
        self.host = os.environ["MYSQL_HOST"]
        self.port = int(os.environ.get("MYSQL_PORT", "3306"))
        self.database = os.environ.get("MYSQL_DB", "reviewdb")
        self.user = os.environ.get("MCP_DB_USER", "mcp_user")
        self.password = os.environ["MCP_DB_PASSWORD"]

    def _connect(self) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
        )

    @staticmethod
    def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
        """MySQL date/datetime/Decimal 값을 JSON 직렬화 가능한 값으로 변환한다."""
        converted: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (date, datetime)):
                converted[key] = value.isoformat()
            elif isinstance(value, Decimal):
                converted[key] = float(value)
            else:
                converted[key] = value
        return converted

    def get_latest_reviews(self, limit: int) -> list[dict[str, Any]]:
        sql = """
            SELECT id, rating, review_date, review, review_length, collected_at
            FROM kakao_reviews
            ORDER BY review_date DESC, id DESC
            LIMIT %s
        """
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (limit,))
                return [self._json_safe(row) for row in cursor.fetchall()]

    def search_reviews(
        self,
        keyword: str,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        where = ["review LIKE %s"]
        params: list[Any] = [f"%{keyword}%"]

        if start_date is not None:
            where.append("review_date >= %s")
            params.append(start_date)
        if end_date is not None:
            where.append("review_date <= %s")
            params.append(end_date)

        params.append(limit)
        sql = f"""
            SELECT id, rating, review_date, review, review_length, collected_at
            FROM kakao_reviews
            WHERE {' AND '.join(where)}
            ORDER BY review_date DESC, id DESC
            LIMIT %s
        """

        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return [self._json_safe(row) for row in cursor.fetchall()]

    def aggregate_ratings(self, start_date: str, end_date: str) -> dict[str, Any]:
        summary_sql = """
            SELECT
                COUNT(*) AS review_count,
                AVG(rating) AS average_rating,
                MIN(rating) AS min_rating,
                MAX(rating) AS max_rating
            FROM kakao_reviews
            WHERE review_date BETWEEN %s AND %s
        """
        distribution_sql = """
            SELECT rating, COUNT(*) AS count
            FROM kakao_reviews
            WHERE review_date BETWEEN %s AND %s
            GROUP BY rating
            ORDER BY rating
        """

        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(summary_sql, (start_date, end_date))
                summary = self._json_safe(cursor.fetchone())

                cursor.execute(distribution_sql, (start_date, end_date))
                distribution_rows = cursor.fetchall()

        summary["rating_distribution"] = {
            str(row["rating"]): int(row["count"]) for row in distribution_rows
        }
        return summary
