from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import os
from utils.logger import setup_logger
from selenium.webdriver.common.action_chains import ActionChains

class GoogleMapsCrawler(BaseCrawler):
    """
    구글맵 리뷰 크롤러
    Selenium을 활용하여 구글맵의 리뷰 화면을 스크롤하면서
    500개의 리뷰(작성일, 별점, 본문 텍스트)를 수집한다.
    수집된 데이터는 csv 파일에서 열 때 파일 손상이나 표 구조 깨짐이 발생하지 않도록
    특수 기호, 이모티콘, 제어 문자 등을 전처리한 후 저장한다.
    """
    def __init__(self, output_dir: str):
        """크롤러 초기 상태 설정"""
        super().__init__(output_dir)
         #구글맵 경복궁 리뷰 URL
        self.base_url = (
            "https://www.google.com/maps/search/%EA%B2%BD%EB%B3%B5%EA%B6%81?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"
        )

        self.reviews_data: list[dict[str, str]] = []    
        self.driver = None
        # 진행 상황이나 에러 메시지를 'google_map.log' 파일에 기록하기 위한 로거(logger) 설정
        self.logger = setup_logger('google_map.log')

        
    def start_browser(self):
        """
        크롤링을 위한 크롬 브라우저를 설정하고 실행하는 함수
        구글맵 리뷰가 한국어로 수집되도록 언어를 설정하고, 
        페이지 로딩에 대비한 대기 시간을 지정
        """
        self.logger.info("브라우저 설정 시작")
        # 브라우저 추가 설정을 위한 객체 생성 
        chrome_options = Options()
        # 구글맵에서 리뷰가 기본적으로 한국어로 보이도록 브라우저 언어를 한국어로 강제 설정
        chrome_options.add_argument("--lang=ko_KR")
        self.driver= webdriver.Chrome(options=chrome_options) #크롬 브라우저 실행
        self.driver.implicitly_wait(5)
        self.logger.info("브라우저가 성공적으로 실행됨")    

    
    def scrape_reviews(self):
        """
        구글맵 페이지에 접속하여 대상 장소(경복궁)의 리뷰를 실시간으로 수집하는 함수
        자동으로 스크롤을 내리며 화면에 로딩된 리뷰(날짜, 별점, 본문)를 추출하고,
        target_count(500개)에 도달하거나 더 이상 스크롤이 되지 않으면 수집을 종료
        """

        self.start_browser()

        self.logger.info("크롤링 시작")
        try:
            self.driver.get(self.base_url) # 구글맵 리뷰 주소로 접속
            time.sleep(5) # 리뷰창 띄우는데 걸리는 시간 기다려주기

            # 구글 리뷰 URL로 바로 접속해도 구글맵에서 리뷰탭으로 바로 연결해주지 않아
            # 아래와 같은 방법으로 리뷰 탭 접속
            try:
                # 첫번째 검색 결과 장소를 클릭하여 상세정보 창으로 이동
                first_result = self.driver.find_element(By.XPATH, '(//*[@role="article"])[1]')
                action = ActionChains(self.driver)
                action.double_click(first_result).perform()
                time.sleep(4)

                # 장소 상세정보 창에서 '리뷰' 탭으로 접속
                review_tab = self.driver.find_element(By.XPATH, "//*[@role='tab' and contains(., '리뷰')]")
                review_tab.click()
                time.sleep(3)
            except Exception as e:
                self.logger.error(f"리뷰 탭 열기 에러: {e}")

            # 중복 수집 방지를 위한 리뷰 ID 저장소
            seen_reviews = set() 
            #이전 루프의 데이터 개수
            last_review_count = 0
            # 스크롤이 헛도는 횟수(새로운 리뷰가 로딩 안될 때)
            scroll_attempts = 0 
            # 수집하고자 하는 목표 리뷰 개수
            target_count = 500 

            while True:
                # 현재 화면에 로딩된 모든 리뷰 박스들을 긁어옴(리뷰 박스 코드:'jftiEf')
                review_blocks = self.driver.find_elements(By.CLASS_NAME, 'jftiEf')
                
                # 스크롤을 내릴 때마다 데이터 추출
                for block in review_blocks:
                    # 구글맵 리뷰의 고유 ID를 가져와서 이미 수집한 리뷰인지 확인
                    review_id = block.get_attribute("data-review-id")
                    if review_id in seen_reviews:
                        continue # 이미 담은 리뷰면 패스
                    
                    seen_reviews.add(review_id) #리뷰 ID 저장소에 추가

                    try:
                        # block 내부에 '자세히 보기' 또는 '더보기' 텍스트를 가진 버튼 요소 탐색
                        more_btn = block.find_element(By.XPATH, ".//button[contains(text(), '자세히 보기') or contains(@aria-label, '자세히 보기') or contains(text(), '더보기')]")
                        # 일반 click()은 화면 가림 현상으로 에러가 날 수 있어 자바스크립트로 강제 클릭
                        self.driver.execute_script("arguments[0].click();", more_btn)
                        time.sleep(0.3)  # 글이 펼쳐져서 렌더링될 때까지 아주 짧게 대기
                    except Exception:
                        pass # 버튼이 없으면(이미 전체 내용이 다 보이는 짧은 리뷰면) 무시하고 넘어감
                    # =====================================================================

                    # 본문 내용 추출(본문 코드:'wiI7pd')
                    try:
                        text = block.find_element(By.CLASS_NAME, 'wiI7pd').get_attribute("textContent").strip()
                    except Exception:
                        text = ""
                        
                    if not text:
                        continue   # 본문이 없는 리뷰는 패스

                    # 별점 추출("aria-label"을 이용하여 텍스트 형태로 추출)
                    try:
                        rating_element = block.find_element(By.CLASS_NAME, 'kvMYJc')
                        rating = rating_element.get_attribute("aria-label")  
                    except Exception:
                        rating = ""

                    # 날짜 추출(날짜 코드: 'rsqaWe' )
                    try:
                        date = block.find_element(By.CLASS_NAME, 'rsqaWe').get_attribute("textContent").strip()
                    except Exception:
                        date = ""

                    # 리뷰 데이터를 날짜, 별점, 본문 별로 저장
                    self.reviews_data.append({
                        "date": date,
                        "rating": rating,
                        "review": text
                    })

                # 현재까지 모은 리뷰 개수 확인
                current_review_count = len(self.reviews_data)
                print(f"현재 수집된 리뷰 개수: {current_review_count} / 목표: {target_count}")

                # 리뷰 500개 이상 모았으면 크롤링 종료
                if current_review_count >= target_count:
                    break

                # 새로운 리뷰가 로딩되지 않으면 크롤링 종료
                if current_review_count == last_review_count:
                    scroll_attempts += 1
                    if scroll_attempts >= 5: 
                        print("더 이상 새로운 리뷰가 로딩되지 않아 수집을 종료합니다.")
                        break
                else:
                    scroll_attempts = 0

                last_review_count = current_review_count

                # 파이썬으로 스크롤기능을 구현했을 때 구글맵 화면이 사진이나 특정 스크롤이 안되는 곳에 맞춰져
                # 중간에 크롤링이 중단되는 문제가 있어 자바스크립트 사용
                if review_blocks:
                    last_block = review_blocks[-1]
                    # 파이썬을 거치지 않고 웹 브라우저에 직접 주입할 자바스크립트 명령어
                    scroll_script = """
                    //해당 화면의 마지막 리뷰
                    var el = arguments[0];

                    // 리뷰의 부모요소
                    var parent = el.parentNode;

                    // 부모 요소들을 거슬러 올라가며 스크롤이 가능한 상자를 찾기
                    while (parent != null) {
                        var style = window.getComputedStyle(parent);
                        //세로 스크롤이 가능한지 확인
                        if (style.overflowY === 'scroll' || style.overflowY === 'auto') {
                            // 스크롤 상자를 찾으면 스크롤바를 맨 밑(scrollHeight)으로 내림
                            parent.scrollTop = parent.scrollHeight;
                            return; 
                        }
                        // 스크롤 상자 못찾으면 상위 부모 요소로 올라가 다시 탐색
                        parent = parent.parentNode;
                    }
                    // 만약 못 찾으면 파이썬에서 쓰던 방식 사용
                    el.scrollIntoView(false);
                    """
                    # 브라우저에 스크롤 스크립트와 last_block을 전달하여 실행
                    self.driver.execute_script(scroll_script, last_block)
                    time.sleep(5)
            
        #에러가 났을 때 프로그램이 터지는 것을 방지, 어떤 에러인지 logger에 기록
        except Exception as e:
            self.logger.error("에러 발생:{e}")

            # 에러가 나면 현재까지 크롤링한 데이터 저장       
            if self.reviews_data:
                self.logger.info("중단된 시점까지의 데이터를 저장")
                self.save_to_database() 

    
    def save_to_database(self):
        """
        수집된 리뷰 데이터를 파일이 손상되지 않도록 전처리한 후 CSV 파일로 저장하는 함수.
        CSV 파일을 열 때 파일 구조가 깨지거나 파일 손상 오류가 발생하는 것을 막기 위해
        내부의 특수 문자, 이모티콘, 수식 기호 등을 정제
        """
        self.logger.info("데이터 저장 시작")

        try:
            import os
            import pandas as pd
            # 리스트에 담긴 딕셔너리 형태의 리뷰를 데이터프레임으로 변환
            df = pd.DataFrame(self.reviews_data)

            # csv 파일이 깨지는 것을 방지하기 위한 장치
            if 'review' in df.columns:
                # 1. 쌍따옴표를 홑따옴표로 변환
                df['review'] = df['review'].astype(str).str.replace('"', "'")
                
                # 2. 한글, 영문, 숫자, 공백, 기본 문장 부호(.,!?'"-~())를 제외한 모든 문자(이모티콘 등) 제거
                # csv 파일에서 인식하지 못하는 이모티콘 때문에 파일이 자꾸 손상되어서 이 과정을 추가함. 
                df['review'] = df['review'].str.replace(r'[^\w\s.,!?\'"\-~()]', ' ', regex=True)
                
                # 3. 엑셀 제어문자 및 줄바꿈 기호 제거
                df['review'] = df['review'].str.replace(r'[\r\n\x00-\x1F\x7F]', ' ', regex=True)
                
                # 4. 수식 기호 앞에 작은따옴표를 붙여 수식 무력화(파일 열었을 때 작은따옴표는 보이지 않음)
                df['review'] = df['review'].apply(lambda x: f"'{x}" if str(x).startswith(('=', '+', '-', '@')) else x)

            file_name = "reviews_GoogleMaps.csv"
            # 결과물을 저장할 폴더 생성 (exist_ok=True 옵션으로 이미 폴더가 있어도 에러 발생 안 함)
            os.makedirs(self.output_dir, exist_ok=True)
            save_path = os.path.join(self.output_dir, file_name)
            # 글자 깨짐 방지를 위해 한글 인코딩 적용
            df.to_csv(save_path, index=False, encoding='utf-8-sig')

            self.logger.info(f"위치 {save_path}로 저장 완료")

        except Exception as e:
            self.logger.error(f"데이터 저장 중 에러 발생: {e}")