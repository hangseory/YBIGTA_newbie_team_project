import pandas as pd
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from base_processor import BaseDataProcessor 

class KakaoMapProcessor(BaseDataProcessor):
    """
    카카오 맵 리뷰 데이터를 전처리하고 파생 변수 생성 및 저장.
    BaseDataProcessor를 상속받아 구현.
    """
    def __init__(self, input_path: str, output_dir: str):
        """
        KakaoMapProcessor 인스턴스 

        Args:
            input_path (str): 원본 카카오맵 리뷰 데이터 CSV 파일의 경로.
            output_dir (str): 전처리된 데이터를 저장할 디렉토리 경로.
        """
        super().__init__(input_path, output_dir)
        self.df = None

    def preprocess(self):
        """
        리뷰 데이터의 결측치 제거, 텍스트 정제, 별점 및 날짜 전처리를 수행

        Returns:
            pd.DataFrame: 전처리가 완료된 데이터프레임.
        """
        self.df = pd.read_csv(self.input_path)
        
        # 1. 리뷰, 날짜가 아예 없는 행은 제거
        self.df = self.df.dropna(subset=['review', 'date'])
        
        # 2. 리뷰 텍스트 정제 (이모티콘 및 불필요한 특수문자 제거)
        if 'review' in self.df.columns:
            self.df['review'] = self.df['review'].apply(self._clean_text)
            # 텍스트가 모두 지워져 빈 문자열만 남은 경우 제거
            self.df = self.df[self.df['review'] != '']
        
        # 3. 별점 전처리 및 결측치 처리
        if 'rating' in self.df.columns:
            self.df['rating'] = pd.to_numeric(self.df['rating'], errors='coerce')
            mean_rating = self.df['rating'].mean()
            fill_value = round(mean_rating) if not pd.isna(mean_rating) else 0
            self.df['rating'] = self.df['rating'].fillna(fill_value).astype(int)
        
        # 4. 날짜 데이터 전처리 ('2025.10.09' 형태를 'YYYY-MM-DD'로 표준화)
        if 'date' in self.df.columns:
            # 온점(.)을 하이픈(-)으로 바꾸고 datetime으로 변환
            self.df['date'] = self.df['date'].astype(str).str.replace('.', '-', regex=False)
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            self.df['date'] = self.df['date'].dt.strftime('%Y-%m-%d')
            # 변환 과정에서 잘못된 형식으로 NaT가 된 행 제거
            self.df = self.df.dropna(subset=['date'])
            
        return self.df

    def _clean_text(self, text):
        """
        텍스트 내의 이모티콘 및 불필요한 특수문자를 제거.

        Args:
            text (str): 원본 리뷰 텍스트.

        Returns:
            str: 정제된 텍스트.
        """
        if pd.isna(text):
            return ""
        
        text = str(text)
        # 한글, 영문, 숫자, 기본 구두점(.,?!) 및 공백을 제외한 모든 문자(이모티콘 등) 제거
        text = re.sub(r'[^가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s.,?!]', '', text)
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def feature_engineering(self):
        """
        리뷰 길이에 대한 파생 변수를 생성하고 이상치 처리 메서드를 호출.

        Returns:
            pd.DataFrame: 파생 변수가 추가되고 이상치가 처리된 데이터프레임.
        """
        if self.df is not None and 'review' in self.df.columns:
            # 텍스트 길이를 세어 새로운 파생 변수로 추가
            self.df['review_length'] = self.df['review'].astype(str).apply(len)
        
        self.handle_outliers()
        return self.df

    def handle_outliers(self):
        """
        리뷰 길이가 1글자인 데이터만 제거 (상한선 제거 없이 요구사항에 맞춤)

        Returns:
            pd.DataFrame: 이상치가 제거된 데이터프레임.
        """
        if self.df is not None and 'review_length' in self.df.columns:
            # 의미를 파악할 수 없는 1글자 리뷰 제거
            self.df = self.df[self.df['review_length'] >= 2]
            
        return self.df

    def vectorize_text(self):
        """
        리뷰 텍스트 데이터를 TF-IDF 방식으로 벡터화하고, 생성된 행렬과 벡터라이저를 피클 파일로 저장.
        """
        if self.df is not None and 'review' in self.df.columns:
            # TF-IDF 벡터라이저 객체 생성
            vectorizer = TfidfVectorizer(max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(self.df['review'])
        
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 카카오맵 전용 이름으로 피클 파일 저장 (구글맵과 파일명 안 겹치게 분리)
            joblib.dump(vectorizer, os.path.join(self.output_dir, 'kakao_tfidf_vectorizer.pkl'))
            joblib.dump(tfidf_matrix, os.path.join(self.output_dir, 'kakao_tfidf_matrix.pkl'))
        
            return tfidf_matrix

    def save_to_database(self):
        """
        최종 전처리된 데이터프레임을 지정된 디렉토리에 CSV 파일로 저장.
        """
        if self.df is not None:
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, 'processed_reviews_KakaoMap.csv')
            self.df.to_csv(output_file, index=False, encoding='utf-8-sig')