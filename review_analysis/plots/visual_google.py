import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 구글맵 리뷰 파일 불러오기
# (파일 이름이나 경로가 다르면 알맞게 수정해 줘!)
df = pd.read_csv('processed_reviews_GoogleMaps.csv')

# 2. 리뷰 길이(글자 수) 계산하기
text_column = 'review' 
df['review_length'] = df[text_column].astype(str).apply(len)

# 3. 리뷰 길이 통계 요약 (평균, 중앙값, 최솟값, 최댓값 등)
print("=== 구글맵 리뷰 길이 통계 요약 ===")
print(df['review_length'].describe())

# 4. 시각화 (히스토그램과 박스플롯을 위아래로 배치)
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 4-1. 히스토그램 (리뷰 길이 분포)
sns.histplot(df['review_length'], bins=50, kde=True, ax=axes[0], color='skyblue')
axes[0].setTitle('Google Maps Review Length Distribution (Histogram)', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Count', fontsize=11)

# 4-2. 박스플롯 (이상치 및 사분위수 확인)
sns.boxplot(x=df['review_length'], ax=axes[1], color='lightgreen')
axes[1].setTitle('Google Maps Review Length (Boxplot)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Review Length (Character Count)', fontsize=11)

plt.tight_layout()
plt.show()










    



