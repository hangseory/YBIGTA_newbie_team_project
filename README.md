# 경복궁 리뷰 크롤링

경복궁 리뷰를 여러 사이트에서 수집하는 프로젝트입니다.

## 데이터

| 사이트 | 링크 | 파일 | 리뷰 개수 |
|---|---|---|---:|
| 카카오맵 | https://place.map.kakao.com/18619553 | `reviews_kakao.csv` | 500개 |
| 트립어드바이저 | https://www.tripadvisor.co.kr/Attraction_Review-g294197-d324888-Reviews-Gyeongbokgung_Palace-Seoul.html | `reviews_트립어드바이저.csv` | 500개 |
| 구글맵스 | https://www.google.co.kr/maps/place/%EA%B2%BD%EB%B3%B5%EA%B6%81/data=!4m10!1m2!2m1!1z6rK967O16raB!3m6!1s0x357ca2c74aeddea1:0x8b3046532cc715f6!8m2!3d37.579617!4d126.977041!15sCgnqsr3rs7XqtoFaCyIJ6rK967O16raBkgERY3VsdHVyYWxfbGFuZG1hcmvgAQA!16zL20vMDJ2M3Q2?entry=ttu&g_ep=EgoyMDI2MDcyMS4wIKXMDSoASAFQAw%3D%3D | `reviews_GoogleMaps.csv` | 500개 |


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



#### 1.3.2 리뷰 길이 분포

![구글맵 리뷰 길이 분포](review_analysis/plots/google_review_length.png)


#### 1.3.3 월별 리뷰 수 변화

![구글맵 월별 리뷰 수](review_analysis/plots/google_monthly.png)

