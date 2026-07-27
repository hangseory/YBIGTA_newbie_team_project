"""트립어드바이저(경복궁) 리뷰 원본 데이터 EDA 스크립트.

명세에서 요구하는 두 가지만 수행합니다.
  1. 분포 파악: 별점, 텍스트 길이, 날짜 분포
  2. 이상치 파악: 별점 범위 이탈, 비정상적으로 길거나 짧은 리뷰, 이상한 날짜(너무 먼 과거/미래)

그래프는 review_analysis/plots/ 에 저장됩니다.
실행: 레포 루트(YBIGTA_newbie_team_project)에서 python review_analysis/eda_tripadvisor.py
"""

import os
import platform
import re

import matplotlib.pyplot as plt
import pandas as pd

# --- 한글 폰트 설정 (OS별로 다르게) ---
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system_name == "Darwin":  # macOS
    plt.rcParams["font.family"] = "AppleGothic"
else:  # Linux
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

INPUT_PATH = os.path.join("database", "reviews_트립어드바이저.csv")
PLOTS_DIR = os.path.join("review_analysis", "plots")
SITE_NAME = "tripadvisor"

RATING_MIN, RATING_MAX = 1, 5
# 날짜 이상치 기준: 트립어드바이저 서비스 시작(2000년) ~ 오늘
DATE_LOWER_BOUND = pd.Timestamp("2000-01-01")


def parse_korean_date(text: str) -> pd.Timestamp:
    """'2024년 11월 14일' -> Timestamp. 파싱 실패 시 NaT."""
    match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", str(text))
    if not match:
        return pd.NaT
    year, month, day = map(int, match.groups())
    try:
        return pd.Timestamp(year=year, month=month, day=day)
    except ValueError:
        return pd.NaT


def load_raw(input_path: str = INPUT_PATH) -> pd.DataFrame:
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    df["parsed_date"] = df["date"].apply(parse_korean_date)
    df["text_length"] = df["content"].astype(str).str.len()
    return df


def report_distributions(df: pd.DataFrame) -> None:
    print("=== 분포 파악 ===")
    print(f"전체 리뷰 수: {len(df)}")
    print("\n[별점 분포]")
    print(df["rating"].value_counts().sort_index())
    print("\n[텍스트 길이 분포]")
    print(df["text_length"].describe())
    print("\n[날짜 범위]")
    print(f"최소: {df['parsed_date'].min()}  /  최대: {df['parsed_date'].max()}")


def report_outliers(df: pd.DataFrame) -> None:
    print("\n=== 이상치 파악 ===")

    rating_outliers = df[(df["rating"] < RATING_MIN) | (df["rating"] > RATING_MAX)]
    print(f"별점 범위({RATING_MIN}~{RATING_MAX}) 벗어난 리뷰: {len(rating_outliers)}개")

    # 텍스트 길이 이상치: IQR 기준
    q1, q3 = df["text_length"].quantile([0.25, 0.75])
    iqr = q3 - q1
    low_cut, high_cut = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    length_outliers = df[(df["text_length"] < low_cut) | (df["text_length"] > high_cut)]
    print(
        f"텍스트 길이 이상치 (IQR 기준, [{low_cut:.1f}, {high_cut:.1f}] 밖): "
        f"{len(length_outliers)}개"
    )
    very_short = df[df["text_length"] <= 2]
    print(f"  - 그 중 1~2자짜리 극단적으로 짧은 리뷰: {len(very_short)}개")

    date_na = df["parsed_date"].isna().sum()
    now = pd.Timestamp.now()
    date_outliers = df[
        df["parsed_date"].notna()
        & ((df["parsed_date"] < DATE_LOWER_BOUND) | (df["parsed_date"] > now))
    ]
    print(f"날짜 파싱 실패(결측 취급): {date_na}개")
    print(f"날짜 이상치 ({DATE_LOWER_BOUND.date()} 이전 또는 미래 날짜): {len(date_outliers)}개")


def plot_distributions(df: pd.DataFrame, plots_dir: str = PLOTS_DIR) -> None:
    os.makedirs(plots_dir, exist_ok=True)

    # 1. 별점 분포
    fig, ax = plt.subplots(figsize=(5, 4))
    rating_counts = (
        df["rating"].value_counts().reindex(range(RATING_MIN, RATING_MAX + 1), fill_value=0)
    )
    rating_counts.plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_title(f"{SITE_NAME} 별점 분포")
    ax.set_xlabel("별점")
    ax.set_ylabel("리뷰 수")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, f"{SITE_NAME}_rating.png"), dpi=150)
    plt.close(fig)

    # 2. 텍스트(리뷰) 길이 히스토그램
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["text_length"], bins=30, color="#55A868")
    ax.set_title(f"{SITE_NAME} 리뷰 길이 분포")
    ax.set_xlabel("글자 수")
    ax.set_ylabel("빈도")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, f"{SITE_NAME}_review_length.png"), dpi=150)
    plt.close(fig)

    # 3. 텍스트 길이 boxplot (이상치 확인용, 별도 파일)
    fig, ax = plt.subplots(figsize=(4, 5))
    ax.boxplot(df["text_length"], vert=True)
    ax.set_title(f"{SITE_NAME} 리뷰 길이 Boxplot")
    ax.set_ylabel("글자 수")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, f"{SITE_NAME}_Boxplot.png"), dpi=150)
    plt.close(fig)

    # 4. 월별 리뷰 수 추이
    monthly = (
        df.dropna(subset=["parsed_date"])
        .set_index("parsed_date")
        .resample("MS")
        .size()
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    monthly.plot(ax=ax, color="#C44E52", marker="o", markersize=3)
    ax.set_title(f"{SITE_NAME} 월별 리뷰 수 추이")
    ax.set_xlabel("작성 월")
    ax.set_ylabel("리뷰 수")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, f"{SITE_NAME}_monthly.png"), dpi=150)
    plt.close(fig)

    print(f"\n그래프 4종을 {plots_dir} 에 저장했습니다.")


def main() -> None:
    df = load_raw()
    report_distributions(df)
    report_outliers(df)
    plot_distributions(df)


if __name__ == "__main__":
    main()
