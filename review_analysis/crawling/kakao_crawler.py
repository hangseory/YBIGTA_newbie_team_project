import csv
import os
import time
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from review_analysis.crawling.base_crawler import BaseCrawler


class KakaoCrawler(BaseCrawler):
    """카카오맵에서 경복궁 리뷰를 수집하는 크롤러."""

    def __init__(self, output_dir: str):
        """크롤러에 필요한 값을 초기화한다."""
        super().__init__(output_dir)

        self.base_url :str = "https://place.map.kakao.com/18619553#review"
        self.driver: Optional[WebDriver] = None
        self.reviews: List[Dict[str, str]] = []

    def start_browser(self) -> None:
        """Chrome 브라우저를 실행한다."""
        chrome_options = webdriver.ChromeOptions()

        self.driver = webdriver.Chrome(
            options=chrome_options,
        )

        
    def scrape_reviews(self):
        """경복궁 리뷰를 수집한다."""
        self.start_browser()
        assert self.driver is not None

        self.driver.get(self.base_url)
        time.sleep(3)

        # 리뷰를 추가로 불러오기 위해 아래로 스크롤
        for _ in range(50):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(3)

        time.sleep(5)
        
        review_items = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.area_review",
        )

        for item in review_items:
            date_elements = item.find_elements(
                By.CSS_SELECTOR,
                "span.txt_date",
            )

            review_elements = item.find_elements(
                By.CSS_SELECTOR,
                "p.desc_review",
            )

            rating_elements = item.find_elements(
                By.CSS_SELECTOR,
                "span.starred_grade span.screen_out",
            )

             # 리뷰 글, 날짜, 별점 중 하나라도 없으면 건너뜀
            if (
                not date_elements
                or not review_elements
                or len(rating_elements) < 2
            ):
                continue

            rating = rating_elements[1].get_attribute("textContent")

            self.reviews.append({
                "rating": rating.strip() if rating else "",
                "date": date_elements[0].text.strip(),
                "review": review_elements[0].text.strip(),
            })

        
        print("찾은 리뷰 항목:", len(review_items))
        print("저장할 리뷰:", len(self.reviews))

        self.driver.quit()

    def save_to_database(self):
        """수집한 리뷰를 CSV 파일로 저장한다."""
        os.makedirs(self.output_dir, exist_ok=True)

        output_path = os.path.join(
            self.output_dir,
            "reviews_kakao.csv",
        )

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["rating", "date", "review"],
            )

            writer.writeheader()
            writer.writerows(self.reviews)