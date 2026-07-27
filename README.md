# 경복궁 리뷰 크롤링

경복궁 리뷰를 여러 사이트에서 수집하는 프로젝트입니다.

## 데이터

| 사이트 | 링크 | 파일 | 리뷰 개수 |
|---|---|---|---:|
| 카카오맵 | https://place.map.kakao.com/18619553 | `reviews_kakao.csv` | 500개 |
| 트립어드바이저 | https://www.tripadvisor.co.kr/Attraction_Review-g294197-d324888-Reviews-Gyeongbokgung_Palace-Seoul.html | `reviews_트립어드바이저.csv` | 500개 |
| 구글맵스 | https://www.google.com/maps/search/%EA%B2%BD%EB%B3%B5%EA%B6%81?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D | `reviews_GoogleMaps.csv` | 500개 |


각 CSV 파일은 다음 컬럼을 포함합니다.

| 컬럼 | 내용 |
|---|---|
| `rating` | 별점 |
| `date` | 작성 날짜 |
| `review` | 리뷰 내용 |

결과 파일은 `database` 폴더에 저장됩니다.

```text
database/
├── reviews_kakao.csv
├── reviews_트립어드바이저.csv
└── reviews_GoogleMaps.csv
```

## 설치

```bash
python -m pip install -r requirements.txt
```

## 실행

카카오맵 크롤러:

```bash
python -m review_analysis.crawling.main -o database -c kakao
```
트립어드바이저 크롤러:

```bash
python -m review_analysis.crawling.main -o database -c tripadvisor
```
구글맵스 크롤러:

```bash
python -m review_analysis.crawling.main -o database -c googlemaps
```

전체 크롤러:

```bash
python -m review_analysis.crawling.main -o database --all
```

## 타입 검사

```bash
python -m mypy review_analysis utils
```

# [4회차] EDA&FE, 시각화 과제

## 1. EDA

### 1.1 카카오맵 리뷰 분석

#### 1.1.1 별점 분포

![카카오맵 별점 분포](review_analysis/plots/kakao_rating.png)

별점은 5점에 매우 집중되어 있고 4점이 그다음으로 많다. 1~3점 리뷰는 상대적으로 매우 적어 전체적으로 높은 별점에 치우친 분포를 보인다. 낮은 별점 리뷰는 개수가 적어 이상치처럼 보일 수 있지만 실제로 부정적인 평가일 수 있으므로 제거 대상보다는 별도로 내용을 확인할 필요가 있다.

#### 1.1.2 리뷰 길이 분포

![카카오맵 리뷰 길이 분포](review_analysis/plots/kakao_review_length.png)

대부분의 리뷰는 비교적 짧은 길이에 집중되어 있으며 리뷰 길이가 길어질수록 개수가 급격히 감소하는 오른쪽 꼬리가 긴 분포를 보인다. 약 700자, 1100자, 1800자 정도의 매우 긴 리뷰가 이상치 후보로 나타난다. 다만 실제로 상세하게 작성된 리뷰로 생각되어 원문을 확인해야 한다.

#### 1.1.3 월별 리뷰 수 변화

![카카오맵 월별 리뷰 수](review_analysis/plots/kakao_monthly.png)

과거에는 월별 리뷰 수가 적었지만 2021년 이후 점차 증가했으며 2023년 이후에는 리뷰 수가 크게 늘어난 모습을 보인다. 일부 월에는 리뷰 수가 갑자기 증가하거나 0에 가까워지는 구간이 존재한다. 이러한 급격한 변화는 이상치 후보이지만 여행 성수기와 비성수기의 영향일 수 있다고 생각된다.

---

### 1.2 트립어드바이저 리뷰 분석

#### 1.2.1 별점 분포

![트립어드바이저 별점 분포](review_analysis/plots/tripadvisor_rating.png)



#### 1.2.2 리뷰 길이 분포

![트립어드바이저 리뷰 길이 분포](review_analysis/plots/tripadvisor_review_length.png)



#### 1.2.3 월별 리뷰 수 변화

![트립어드바이저 월별 리뷰 수](review_analysis/plots/tripadvisor_monthly.png)


---

### 1.3 구글맵 리뷰 분석

#### 1.3.1 별점 분포

![구글맵 별점 분포](review_analysis/plots/google_rating.png)
별점은 5점이 매우 많고 4점이 다음으로 많다. 1~3점에는 18개의 리뷰밖에 없을정도로 적었다. 별점의 평균은 4.70이다. 낮은 별점 리뷰는 개수가 적어 이상치처럼 보일 수 있지만 실제로 부정적인 평가일 수 있으므로 제거 대상보다는 별도로 내용을 확인할 필요가 있다.


#### 1.3.2 리뷰 길이 분포

![구글맵 리뷰 길이 분포](review_analysis/plots/google_review_length.png)
![구글맵 리뷰 길이 박스 플롯](review_analysis/plots/google_Boxplot.png)



#### 1.3.3 연도별 리뷰 수 변화

![구글맵 월별 리뷰 수](review_analysis/plots/google_yearly.png)


## 2.전처리/FE
### 2.1 공통
1. 결측치 처리 
- 자연어 분석의 핵심인 리뷰 내용(review)이나 작성 날짜(date)가 누락된 데이터는 분석에 활용할 수 없으므로 행 자체를 제거했다.
- 별점 데이터에 결측치가 존재하는 경우, 전체 데이터의 왜곡을 최소화하기 위해 '평균 별점'을 반올림한 정수값으로 대체했다.

2. 이상치 처리
- 1글자로 이루어진 리뷰(예: '.','ㅋ'): 문맥적 정보가 없는 텍스트 이상치로 판단하여 제거했다.
- 글자 수가 매우 많은 리뷰: 먼저 이러한 리뷰들이 모두 스팸, 도배, 광고가 아님을 확인했다. 이러한 리뷰는 이상치로 보기보다는 오히려 상세하고 구체적인 경우가 많아 가치 있는 데이터로 판단내려 제거하지 않았다.   

3. 텍스트 데이터 전처리
- 이모티콘과 불필요한 특수문자 제거: 이모티콘과 불필요한 특수문자는 텍스트 벡터화할 때 차원을 쓸데없이 크게 만들고 시각화하는 과정에서 폰트가 깨지거나 에러를 유발할 수 있기에 지우기로 결정했다. 정규표현식(RegEx)을 사용하여 한글, 영문, 숫자, 기본 구두점(.,?!), 공백을 제외한 모든 불필요한 특수문자와 그림 이모티콘을 텍스트에서 완전히 제거했다. 
- 공백 정제: 연속된 공백을 단일 공백으로 줄이고 문자열 양끝의 불필요한 띄어쓰기를 잘라내어 분석 모델이 단어를 정확히 인식하도록 정제했다. 정제 후 텍스트가 완전히 비어버린 행도 제거했다.

4. 파생변수 생성 
- 리뷰 글자 수: 정제된 리뷰 텍스트의 총 글자 수를 계산하여 새로운 파생변수로 추가했다. 이 변수는 사용자 리뷰의 정성적 깊이를 유추하는 지표이자 이상치를 필터링하기 위한 척도로 활용했다.

5. 텍스트 벡터화
- TF-IDF 적용: 추후 키워드 빈도 분석 및 감정 분석을 수행하기 위해 정제된 리뷰 텍스트를 숫자로 이루어진 Sparse Matrix로 변환하는 TF-IDF 방식을 적용했다.
- 피처 최적화 및 저장: 메모리 효율과 학습 속도를 고려해 출현 빈도 기준 최상위 1,000개의 단어만 피처로 추출했다. 변환된 행렬과 벡터라이저는 .pkl 확장자(joblib)로 저장하여 즉시 분석에 사용할 수 있도록 했다. 

### 2.2 카카오맵 리뷰 전처리
- 텍스트 데이터 전처리 
1. 'YYYY.MM.DD' 형태의 날짜 데이터를 이후 원활한 비교분석을 위해 'YYYY-MM-DD' 형태로    표준화했다.

### 2.3 트립어드바이저 리뷰 전처리
- 텍스트 데이터 전처리 
1. 리뷰 내용의 컬럼명을 'content'에서 'review'로 통일해주었다.
1. 'YYYY년 MM월 DD일' 형태의 날짜 데이터를 이후 원활한 비교분석을 위해 'YYYY-MM-DD' 형태로 표준화했다.

### 2.4 구글맵 리뷰 전처리

- 텍스트 데이터 전처리 
1. 크롤링 된 'n달 전', 'n년 전' 형태의 문자열 날짜를 크롤링 기준일(2026-07-27)을 기준으로 계산하여 시계열 분석이 가능한 형태인 'YYYY-MM-DD' 형식의 날짜로 일괄 변환했다.
2. ‘별표 n개’ 형태의 문자열 데이터를 'n' 형태의 int 데이터로 변환했다. 


# [4회차] GitHub 협업과제

## 1. 팀 소개
저희 8조는 Web, 리뷰 데이터 크롤링, EDA 및 Feature Engineering 과제를 함께 수행했습니다. GitHub의 브랜치 보호 규칙과 Pull Request, 코드 리뷰 과정을 적용하여 협업을 진행했습니다.
### 1.1 팀원 자기소개

- 22학번 컴퓨터과학과 01년생 설승곤입니다.
- 팀원 2:
- 팀원 3:

---

## 2. GitHub 협업 과정

### 2.1 Branch Protection Rule

![브랜치 보호 규칙](github/branch_protection.png)

### 2.2 Main 브랜치 Push 거부

![Main 브랜치 Push 거부](github/push_rejected.png)

### 2.3 Pull Request, Review 및 Merge

![Pull Request Review 및 Merge](github/review_and_merged.png)

---

## 3. 과제 실행 방법

### 3.1 패키지 설치

```bash
python -m pip install -r requirements.txt
```

### 3.2 Web 과제 실행

```bash
uvicorn app.main:app --reload
```

```bash
pytest
```

```bash
mypy app/
```

### 3.3 크롤링 과제 실행

#### 카카오맵

```bash
python -m review_analysis.crawling.main -o database -c kakao
```

#### 트립어드바이저

```bash
python -m review_analysis.crawling.main -o database -c tripadvisor
```

#### 구글맵

```bash
python -m review_analysis.crawling.main -o database -c googlemaps
```

#### 전체 크롤링

```bash
python -m review_analysis.crawling.main -o database --all
```

#### 타입 검사

```bash
python -m mypy review_analysis utils
```

### 3.4 EDA 실행

#### 카카오맵

```bash
python review_analysis/plots/visual_kakao.py
```

#### 트립어드바이저

```bash
python review_analysis/plots/트립어드바이저_시각화파일명.py
```

#### 구글맵

```bash
python review_analysis/plots/구글맵_시각화파일명.py
```

### 3.5 전처리 및 Feature Engineering 실행

```bash
python -m review_analysis.preprocessing.main --output_dir database --all
```
