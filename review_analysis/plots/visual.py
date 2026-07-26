import os

import matplotlib.pyplot as plt
import pandas as pd


df = pd.read_csv("database/reviews_kakao.csv")

os.makedirs("review_analysis/plots", exist_ok=True)

# EDA용 보조값
df["review_length"] = df["review"].fillna("").str.len()
df["date"] = pd.to_datetime(df["date"], errors="coerce")


# 1. 별점 분포
df["rating"].value_counts().sort_index().plot(kind="bar")

plt.title("Kakao Rating Distribution")
plt.xlabel("Rating")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("review_analysis/plots/kakao_rating.png")
plt.close()


# 2. 리뷰 길이 분포
df["review_length"].plot(kind="hist", bins=30)

plt.title("Kakao Review Length Distribution")
plt.xlabel("Review Length")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("review_analysis/plots/kakao_review_length.png")
plt.close()


# 3. 월별 리뷰 수
monthly = (
    df.dropna(subset=["date"])
    .set_index("date")
    .resample("ME")
    .size()
)

monthly.plot(kind="line")

plt.title("Kakao Monthly Review Count")
plt.xlabel("Date")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("review_analysis/plots/kakao_monthly.png")
plt.close()