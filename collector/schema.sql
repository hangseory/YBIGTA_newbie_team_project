-- ============================================================
-- reviewdb 스키마: 카카오맵 리뷰 테이블 + DB 계정 분리
-- 실행 방법 (EC2에서, RDS 엔드포인트에 접속 가능한 상태에서):
--   mysql -h <RDS_ENDPOINT> -P 3306 -u <admin_user> -p reviewdb < schema.sql
--
-- 주의: 아래 <COLLECTOR_PASSWORD>, <MCP_PASSWORD> 는 실행 직전에
-- 실제 비밀번호로 바꿔서 로컬에서만 실행하고, 수정한 버전은 git에 커밋하지 마세요.
-- ============================================================

USE reviewdb;

-- ------------------------------------------------------------
-- 1. 테이블
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kakao_reviews (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rating          TINYINT UNSIGNED NOT NULL,
    review_date     DATE NOT NULL,
    review          TEXT NOT NULL,
    review_length   INT UNSIGNED NOT NULL,
    -- rating + review_date + review 내용을 합쳐 SHA-256 해시로 만든 값.
    -- 같은 리뷰가 여러 번 수집돼도 이 값으로 중복 삽입을 막는다.
    review_hash     CHAR(64) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
    -- 이 리뷰를 마지막으로 수집기가 확인한 시각. 주기적 자동 갱신 증빙에 사용.
    collected_at    DATETIME NOT NULL,
    UNIQUE KEY uq_kakao_reviews_hash (review_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 2. DB 계정 분리
--    collector_user : 수집기 전용, INSERT/UPDATE/SELECT만 가능
--    mcp_user        : MCP 서버 전용, SELECT만 가능 (read-only)
-- ------------------------------------------------------------
CREATE USER IF NOT EXISTS 'collector_user'@'%' IDENTIFIED BY '<COLLECTOR_PASSWORD>';
GRANT SELECT, INSERT, UPDATE ON reviewdb.kakao_reviews TO 'collector_user'@'%';

CREATE USER IF NOT EXISTS 'mcp_user'@'%' IDENTIFIED BY '<MCP_PASSWORD>';
GRANT SELECT ON reviewdb.* TO 'mcp_user'@'%';

FLUSH PRIVILEGES;
