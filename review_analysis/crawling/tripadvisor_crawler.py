"""경복궁 트립어드바이저 리뷰 크롤러.

BaseCrawler를 상속받아 트립어드바이저 관광명소 페이지의 방문자 리뷰를
Selenium(페이지 로딩용) + BeautifulSoup(파싱용)으로 수집하고 CSV로 저장한다.
로그인이나 스크롤/클릭 없이 페이지 주소만 바꿔가며 순회하면 되므로,
requests보다 안정적인 실제 브라우저(Selenium)로 페이지를 연다.
"""

import csv
import os
import re
import time
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger


class TripAdvisorCrawler(BaseCrawler):
    """트립어드바이저 경복궁 리뷰를 크롤링하는 클래스."""

    BASE_URL = "https://www.tripadvisor.co.kr/Attraction_Review-g294197-d324888-Reviews-{offset}Gyeongbokgung_Palace-Seoul.html"
    MIN_REVIEWS = 500
    REVIEWS_PER_PAGE = 10

    def __init__(self, output_dir: str) -> None:
        """크롤러를 초기화한다.

        Args:
            output_dir: 결과 CSV를 저장할 디렉토리 경로.
        """
        super().__init__(output_dir)
        self.reviews: List[Dict[str, str]] = []
        self.logger = setup_logger("tripadvisor_crawler.log")
        self.driver: Optional[WebDriver] = None

    def start_browser(self) -> None:
        """Selenium 브라우저를 켠다. (로그인 불필요, 페이지 이동만 사용)"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.logger.info("브라우저 준비 완료.")

    def _build_url(self, page_index: int) -> str:
        """페이지 번호(0부터 시작)에 해당하는 리뷰 목록 URL을 생성한다."""
        if page_index == 0:
            offset = ""
        else:
            offset = f"or{page_index * self.REVIEWS_PER_PAGE}-"
        return self.BASE_URL.format(offset=offset)

    def scrape_reviews(self) -> None:
        """여러 페이지를 순회하며 리뷰를 수집한다.

        각 페이지에서 리뷰 카드(data-automation="reviewCard")를 찾아
        별점, 작성일, 리뷰 내용을 파싱하여 self.reviews에 저장한다.
        """
        if self.driver is None:
            raise RuntimeError("start_browser()를 먼저 호출해야 합니다.")

        page_index = 0
        empty_page_count = 0

        while len(self.reviews) < self.MIN_REVIEWS:
            url = self._build_url(page_index)
            self.logger.info("페이지 요청: %s", url)

            self.driver.get(url)
            time.sleep(2.5)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            review_cards = soup.select('div[data-automation="reviewCard"]')

            if not review_cards:
                empty_page_count += 1
                self.logger.info("리뷰 카드 없음 (%d회 연속).", empty_page_count)
                if empty_page_count >= 2:
                    self.logger.info("리뷰가 더 없는 것으로 판단, 종료.")
                    break
            else:
                empty_page_count = 0

            for card in review_cards:
                rating = self._parse_rating(card)
                date = self._parse_date(card)
                content = self._parse_content(card)

                if content:
                    self.reviews.append(
                        {"rating": rating, "date": date, "content": content}
                    )

            self.logger.info(
                "%d페이지 처리 완료. 누적 리뷰 수: %d", page_index + 1, len(self.reviews)
            )

            page_index += 1

        self.logger.info("파싱 완료: 총 %d개 리뷰 수집됨.", len(self.reviews))

    def _parse_rating(self, card) -> str:
        """리뷰 카드에서 별점을 추출한다. (예: '풍선 5개 중 5' -> '5')"""
        title_tag = card.select_one('svg[data-automation="bubbleRatingImage"] title')
        if title_tag:
            match = re.search(r"중\s*(\d+)", title_tag.get_text())
            if match:
                return match.group(1)
        return ""

    def _parse_date(self, card) -> str:
        """리뷰 카드에서 작성일을 추출한다. (예: '2026년 2월 21일 작성')"""
        date_tag = card.select_one("div.BNelO div.biGQs")
        if date_tag:
            return date_tag.get_text().replace("작성", "").strip()
        return ""

    def _parse_content(self, card) -> str:
        """리뷰 카드에서 본문 내용을 추출한다."""
        content_tag = card.select_one("span.yCeTE")
        if content_tag:
            for br in content_tag.find_all("br"):
                br.replace_with("\n")
            return content_tag.get_text().strip()
        return ""

    def save_to_database(self) -> None:
        """수집한 리뷰 데이터를 CSV 파일로 저장한다.

        저장 경로: {output_dir}/reviews_트립어드바이저.csv
        컬럼: rating(별점), date(작성일), content(리뷰 내용)
        """
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_트립어드바이저.csv")

        with open(file_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["rating", "date", "content"])
            writer.writeheader()
            for review in self.reviews:
                writer.writerow(review)

        self.logger.info("%d개 리뷰를 %s에 저장 완료.", len(self.reviews), file_path)

        if self.driver:
            self.driver.quit()
            self.logger.info("브라우저 종료.")