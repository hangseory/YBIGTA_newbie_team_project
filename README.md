# 경복궁 리뷰 크롤링

경복궁 리뷰를 여러 사이트에서 수집하는 프로젝트입니다.

## 데이터

| 사이트 | 링크 | 파일 | 리뷰 개수 |
|---|---|---|---:|
| 카카오맵 | https://place.map.kakao.com/18619553 | `reviews_kakao.csv` | 500개 |
| 트립어드바이저 | https://www.tripadvisor.co.kr/Attraction_Review-g294197-d324888-Reviews-Gyeongbokgung_Palace-Seoul.html | `reviews_트립어드바이저.csv` | 500개 |
| [사이트명] | [링크] | `reviews_[사이트명].csv` | [개수] |
| [사이트명] | [링크] | `reviews_[사이트명].csv` | [개수] |

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
└── reviews_[사이트명].csv
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

전체 크롤러:

```bash
python -m review_analysis.crawling.main -o database --all
```

## 타입 검사

```bash
python -m mypy review_analysis utils
```