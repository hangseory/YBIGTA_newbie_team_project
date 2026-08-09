import pandas as pd
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from review_analysis.preprocessing.base_processor import BaseDataProcessor 

class TripAdvisorProcessor(BaseDataProcessor):
    """
    트립어드바이저 리뷰 데이터를 전처리하고 파생 변수 생성 및 저장
    BaseDataProcessor를 상속받아 구현.
    """
    def __init__(self, input_path: str, output_dir: str):
        """
        TripAdvisorProcessor 인스턴스 초기화

        Args:
            input_path (str): 원본 트립어드바이저 리뷰 데이터 CSV 파일의 경로.
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
        
        # 1. 트립어드바이저는 리뷰 컬럼명이 'content'이므로 'review'로 통일
        if 'content' in self.df.columns and 'review' not in self.df.columns:
            self.df = self.df.rename(columns={'content': 'review'})
        
        # 2. 리뷰, 날짜가 아예 없는 행은 제거
        self.df = self.df.dropna(subset=['review', 'date'])
        
        # 3. 리뷰 텍스트 정제 (이모티콘 및 불필요한 특수문자 제거)
        if 'review' in self.df.columns:
            self.df['review'] = self.df['review'].apply(self._clean_text)
            # 텍스트가 모두 지워져 빈 문자열만 남은 경우 제거
            self.df = self.df[self.df['review'] != '']
        
        # 4. 별점 전처리 및 결측치 처리 (숫자형태 데이터 평균 반올림 적용)
        if 'rating' in self.df.columns:
            self.df['rating'] = pd.to_numeric(self.df['rating'], errors='coerce')
            # 이상치 처리: 1~5점 범위 벗어난 값은 결측 처리
            self.df.loc[
                (self.df['rating'] < 1) | (self.df['rating'] > 5), 'rating'
            ] = pd.NA
            mean_rating = self.df['rating'].mean()
            fill_value = round(mean_rating) if not pd.isna(mean_rating) else 0
            self.df['rating'] = self.df['rating'].fillna(fill_value).astype(int)

        # 5. 날짜 데이터 전처리 ('2017년 6월 11일' 형태를 'YYYY-MM-DD'로 표준화)
        if 'date' in self.df.columns:
            self.df['date'] = self.df['date'].astype(str)
            # '년', '월'을 '-'로 바꾸고 '일'을 제거
            self.df['date'] = self.df['date'].str.replace(r'년\s*', '-', regex=True)
            self.df['date'] = self.df['date'].str.replace(r'월\s*', '-', regex=True)
            self.df['date'] = self.df['date'].str.replace(r'일', '', regex=True)
            self.df['date'] = self.df['date'].str.strip() # 공백 제거
            
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            self.df = self.df.dropna(subset=['date'])

            # 이상치 처리: 너무 오래되거나(2000년 이전) 미래 날짜 제거
            now = pd.Timestamp.now()
            self.df = self.df[
                (self.df['date'] >= pd.Timestamp('2000-01-01')) & (self.df['date'] <= now)
            ]
            self.df['date'] = self.df['date'].dt.strftime('%Y-%m-%d')
            
        return self.df

    def _clean_text(self, text):
        """
        텍스트 내의 이모티콘 및 불필요한 특수문자를 제거

        Args:
            text (str): 원본 리뷰 텍스트.

        Returns:
            str: 정제된 텍스트.
        """
        if pd.isna(text):
            return ""
        
        text = str(text)
        # 한글, 영문, 숫자, 기본 구두점(.,?!) 및 공백을 제외한 모든 문자 제거
        text = re.sub(r'[^가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s.,?!]', '', text)
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def feature_engineering(self):
        """
        리뷰 길이에 대한 파생 변수를 생성하고 이상치 처리 메서드를 호출

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
        리뷰 길이가 1글자인 데이터만 제거 (상한선 제한 없음)

        Returns:
            pd.DataFrame: 이상치가 처리된 데이터프레임.
        """
        if self.df is not None and 'review_length' in self.df.columns:
            # 1글자 리뷰 제거
            self.df = self.df[self.df['review_length'] >= 2]
            
        return self.df

    def vectorize_text(self):
        """
        리뷰 텍스트 데이터를 TF-IDF 방식으로 벡터화하고, 생성된 행렬과 벡터라이저를 피클 파일로 저장.
        """
        if self.df is not None and 'review' in self.df.columns:
            vectorizer = TfidfVectorizer(max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(self.df['review'])
        
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 트립어드바이저 전용 파일명으로 피클 저장
            joblib.dump(vectorizer, os.path.join(self.output_dir, 'tripadvisor_tfidf_vectorizer.pkl'))
            joblib.dump(tfidf_matrix, os.path.join(self.output_dir, 'tripadvisor_tfidf_matrix.pkl'))
        
            return tfidf_matrix

    def save_to_database(self):
        """
        최종 전처리된 데이터프레임을 지정된 디렉토리에 CSV 파일로 저장합니다.
        """
        if self.df is not None:
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, 'preprocessed_reviews_트립어드바이저.csv')
            self.df.to_csv(output_file, index=False, encoding='utf-8-sig')