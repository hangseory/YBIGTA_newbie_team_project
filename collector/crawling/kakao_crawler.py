import csv
import os
import re
import time
from typing import Dict, List, Optional, Set, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from collector.crawling.base_crawler import BaseCrawler


def remove_emoji(text: str) -> str:
    """문자열에서 이모지를 제거한다."""
    emoji_pattern = re.compile(
        "["
        "\U0001F1E6-\U0001F1FF"
        "\U0001F300-\U0001FAFF"
        "☀-⛿"
        "✀-➿"
        "]",
        flags=re.UNICODE,
    )

    cleaned = emoji_pattern.sub("", text)

    return (
        cleaned.replace("️", "")
        .replace("‍", "")
        .strip()
    )


class KakaoCrawler(BaseCrawler):
    """카카오맵에서 경복궁 리뷰를 수집하는 크롤러."""

    TARGET_REVIEW_COUNT = 50
    MAX_SCROLL_COUNT = 30
    MAX_STAGNANT_COUNT = 5

    def __init__(self, output_dir: str) -> None:
        """크롤러에 필요한 값을 초기화한다."""
        super().__init__(output_dir)

        self.base_url: str = (
            "https://place.map.kakao.com/18619553#review"
        )
        self.driver: Optional[WebDriver] = None
        self.reviews: List[Dict[str, str]] = []

    def start_browser(self) -> None:
        """Chrome 브라우저를 headless 모드로 실행한다.

        EC2(Amazon Linux, GUI 없음)에서 동작해야 하므로 headless와
        서버 환경에서 흔히 필요한 옵션들을 함께 지정한다.
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # 설치된 Chrome 버전에 맞는 chromedriver를 자동으로 받아와
        # 버전 불일치 문제를 피한다.
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _expand_current_reviews(self) -> int:
        """현재 DOM에 표시된 긴 리뷰의 더보기를 클릭한다."""
        assert self.driver is not None

        clicked_count = self.driver.execute_script(
            """
            const buttons = Array.from(
                document.querySelectorAll(
                    "div.area_review p.desc_review span.btn_more"
                )
            );

            let clickedCount = 0;

            for (const button of buttons) {
                const style = window.getComputedStyle(button);
                const isVisible =
                    style.display !== "none" &&
                    style.visibility !== "hidden" &&
                    button.getClientRects().length > 0;

                if (
                    !isVisible ||
                    button.textContent.trim() !== "더보기"
                ) {
                    continue;
                }
                button.click();
                clickedCount += 1;
            }

            return clickedCount;
            """
        )

        return int(clicked_count or 0)

    def _collect_current_reviews(
        self,
        seen: Set[Tuple[str, str, str]],
    ) -> int:
        """현재 DOM의 리뷰를 즉시 추출하여 누적 저장한다."""
        assert self.driver is not None

        rows = self.driver.execute_script(
            """
            const reviewItems = Array.from(
                document.querySelectorAll("div.area_review")
            );

            return reviewItems.map((item) => {
                const dateElement =
                    item.querySelector("span.txt_date");
                const reviewElement =
                    item.querySelector("p.desc_review");
                const ratingElements =
                    item.querySelectorAll(
                        "span.starred_grade span.screen_out"
                    );

                if (
                    !dateElement ||
                    !reviewElement ||
                    ratingElements.length < 2
                ) {
                    return null;
                }

                return {
                    rating:
                        ratingElements[1].textContent || "",
                    date:
                        dateElement.innerText ||
                        dateElement.textContent ||
                        "",
                    review:
                        reviewElement.innerText ||
                        reviewElement.textContent ||
                        ""
                };
            }).filter((row) => row !== null);
            """
        )

        new_count = 0

        for row in rows:
            rating = str(row.get("rating", "")).strip()
            date = str(row.get("date", "")).strip()
            review_text = remove_emoji(
                str(row.get("review", ""))
                .replace("더보기", "")
                .replace("접기", "")
                .strip()
            )

            if not review_text:
                continue

            key = (rating, date, review_text)

            if key in seen:
                continue

            seen.add(key)

            self.reviews.append(
                {
                    "rating": rating,
                    "date": date,
                    "review": review_text,
                }
            )
            new_count += 1

        return new_count

    def _scroll_to_next_reviews(self) -> bool:
        """현재 마지막 리뷰까지 이동해 다음 리뷰 로딩을 유도한다."""
        assert self.driver is not None

        review_items = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.area_review",
        )

        if not review_items:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            return False

        self.driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: "end",
                inline: "nearest"
            });
            """,
            review_items[-1],
        )

        self.driver.execute_script(
            "window.scrollBy(0, 900);"
        )

        return True

    def scrape_reviews(self) -> None:
        """더보기 클릭, 추출, 스크롤 순서로 리뷰를 수집한다."""
        self.start_browser()
        assert self.driver is not None

        self.reviews.clear()
        seen: Set[Tuple[str, str, str]] = set()
        stagnant_count = 0

        try:
            self.driver.get(self.base_url)
            time.sleep(3)

            for _ in range(self.MAX_SCROLL_COUNT):
                # 1. 현재 화면의 긴 리뷰를 먼저 펼친다.
                clicked_count = self._expand_current_reviews()

                if clicked_count > 0:
                    time.sleep(0.5)

                # 2. 현재 화면의 리뷰를 즉시 추출해 저장한다.
                new_count = self._collect_current_reviews(seen)

                print(
                    "더보기 클릭:",
                    clicked_count,
                    "| 이번 수집:",
                    new_count,
                    "| 누적 리뷰:",
                    len(self.reviews),
                )

                if len(self.reviews) >= self.TARGET_REVIEW_COUNT:
                    break

                if new_count == 0:
                    stagnant_count += 1
                else:
                    stagnant_count = 0

                if stagnant_count >= self.MAX_STAGNANT_COUNT:
                    print(
                        "새 리뷰가 더 이상 나타나지 않아 "
                        "수집을 종료합니다."
                    )
                    break

                # 3. 현재 리뷰를 저장한 뒤 다음 리뷰로 스크롤한다.
                self._scroll_to_next_reviews()
                time.sleep(2)

            ellipsis_count = sum(
                review["review"].rstrip().endswith("...")
                for review in self.reviews
            )

            print("최종 저장 리뷰:", len(self.reviews))
            print("말줄임표로 끝나는 리뷰:", ellipsis_count)

        finally:
            self.driver.quit()

    def save_to_database(self) -> None:
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

        print(f"저장 완료: {output_path}")
