import logging
import os

from collector.crawling.kakao_crawler import KakaoCrawler
from collector.preprocessing.kakao_processor import KakaoMapProcessor
from collector.db_writer import load_reviews_from_csv, save_reviews

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_CSV_PATH = os.path.join(DATA_DIR, "reviews_kakao.csv")
PROCESSED_CSV_PATH = os.path.join(DATA_DIR, "processed_reviews_KakaoMap.csv")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("collector")


def run() -> None:
    """카카오맵 리뷰를 수집해 전처리한 뒤 RDS에 반영한다.

    systemd timer가 1시간마다 이 함수 하나만 실행하면
    수집 -> 전처리 -> DB 저장까지 한 번에 끝난다.
    """
    logger.info("카카오맵 리뷰 크롤링 시작")
    # KakaoCrawler.scrape_reviews() 내부에서 자체적으로
    # start_browser()를 호출하므로 여기서 별도로 호출하지 않는다.
    crawler = KakaoCrawler(output_dir=DATA_DIR)
    crawler.scrape_reviews()
    crawler.save_to_database()
    logger.info("크롤링 완료: %s", RAW_CSV_PATH)

    logger.info("전처리 시작")
    processor = KakaoMapProcessor(
        input_path=RAW_CSV_PATH,
        output_dir=DATA_DIR,
    )
    processor.preprocess()
    processor.feature_engineering()
    processor.save_to_database()
    logger.info("전처리 완료: %s", PROCESSED_CSV_PATH)

    logger.info("RDS 반영 시작")
    rows = load_reviews_from_csv(PROCESSED_CSV_PATH)
    processed_count = save_reviews(rows)
    logger.info("RDS 반영 완료: %d건 처리(신규 삽입 + 기존 갱신)", processed_count)


if __name__ == "__main__":
    run()
