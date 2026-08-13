"""사이트별 시간대별(월별) 리뷰 수 비교 - 선그래프.

명세 2번(비교분석) 중 '시계열 분석' 항목: 시간대별 리뷰 개수 추이 비교.
database 폴더의 (pre)processed_reviews_*.csv 를 모두 읽어서
사이트별로 겹친 라인그래프를 그린다.

실행: 레포 루트(YBIGTA_newbie_team_project)에서
    python review_analysis/plots/compare_monthly_reviews.py
"""

import glob
import os
import platform

import matplotlib.pyplot as plt
import pandas as pd

# --- 한글 폰트 설정 ---
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system_name == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

DATABASE_DIR = "database"
PLOTS_DIR = os.path.join("review_analysis", "plots")

# 파일명 -> 보기 좋은 사이트 이름으로 매핑
SITE_NAME_MAP = {
    "KakaoMap": "kakao",
    "GoogleMaps": "google",
    "트립어드바이저": "tripadvisor",
}


def load_all_sites(database_dir: str = DATABASE_DIR) -> dict:
    """(pre)processed_reviews_*.csv 를 전부 읽어서 {사이트이름: DataFrame} 형태로 반환."""
    patterns = [
        os.path.join(database_dir, "preprocessed_reviews_*.csv"),
        os.path.join(database_dir, "processed_reviews_*.csv"),
    ]
    site_dfs = {}
    for pattern in patterns:
        for path in glob.glob(pattern):
            base = os.path.basename(path)
            site_raw = (
                base.replace("preprocessed_reviews_", "")
                .replace("processed_reviews_", "")
                .replace(".csv", "")
            )
            if site_raw in site_dfs:
                continue  # 이미 로드된 사이트면 중복 방지
            site_name = SITE_NAME_MAP.get(site_raw, site_raw)

            df = pd.read_csv(path, encoding="utf-8-sig")
            if "date" not in df.columns:
                print(f"[경고] {base} 에 'date' 컬럼이 없어서 건너뜁니다. 컬럼: {list(df.columns)}")
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            site_dfs[site_name] = df
            print(f"로드 완료: {base} -> '{site_name}' ({len(df)}행)")

    return site_dfs


def monthly_counts(site_dfs: dict) -> pd.DataFrame:
    """사이트별 월별 리뷰 수를 하나의 DataFrame으로 합침 (컬럼=사이트, 인덱스=월)."""
    series_dict = {}
    for site_name, df in site_dfs.items():
        monthly = df.set_index("date").resample("MS").size()
        series_dict[site_name] = monthly
    combined = pd.DataFrame(series_dict).fillna(0)
    return combined


def plot_comparison(combined: pd.DataFrame, plots_dir: str = PLOTS_DIR) -> None:
    os.makedirs(plots_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 5))
    for site_name in combined.columns:
        ax.plot(combined.index, combined[site_name], marker="o", markersize=2, label=site_name)

    ax.set_title("사이트별 월별 리뷰 수 비교")
    ax.set_xlabel("작성 월")
    ax.set_ylabel("리뷰 수")
    ax.legend(title="사이트")
    fig.tight_layout()

    out_path = os.path.join(plots_dir, "monthly_review_comparison.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"그래프 저장 완료: {out_path}")


def main() -> None:
    site_dfs = load_all_sites()
    if not site_dfs:
        print("로드된 사이트 데이터가 없습니다. database 폴더 경로/파일명을 확인하세요.")
        return

    combined = monthly_counts(site_dfs)
    print("\n=== 월별 리뷰 수 (사이트별) ===")
    print(combined)

    plot_comparison(combined)


if __name__ == "__main__":
    main()