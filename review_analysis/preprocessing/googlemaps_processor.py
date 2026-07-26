import pandas as pd
import re
import os
from dateutil.relativedelta import relativedelta
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from base_processor import BaseDataProcessor 

class GoogleMapsProcessor(BaseDataProcessor):
    """
    구글 맵 리뷰 데이터를 전처리하고 파생 변수 생성 및 저장.
    BaseDataProcessor를 상속받아 구현.
    """
    def __init__(self, input_path: str, output_dir: str, base_date: str = '2026-07-27'):
        """
        GoogleMapsProcessor 인스턴스 초기화

        Args:
            input_path (str): 원본 리뷰 데이터 CSV 파일의 경로.
            output_dir (str): 전처리된 데이터를 저장할 디렉토리 경로.
            base_date (str, optional): 상대적 날짜 변환의 기준이 되는 날짜. 기본값은 '2026-07-27'.
        """
        super().__init__(input_path, output_dir)
        # 텍스트로 된 날짜('n달 전')를 실제 날짜로 변환할 기준일 설정
        self.base_date = pd.to_datetime(base_date)
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
        
        # 2. 리뷰 텍스트 정제
        if 'review' in self.df.columns:
            self.df['review'] = self.df['review'].apply(self._clean_text)
            # 텍스트가 모두 지워져 빈 문자열만 남은 경우 제거
            self.df = self.df[self.df['review'] != '']
        
        # 3. 별점 전처리 및 결측치 처리
        if 'rating' in self.df.columns:
            self.df['rating'] = self.df['rating'].astype(str).str.extract(r'(\d+)').astype(float)
            # 별점 결측치엔 전체 평균 별점을 반올림하여 채워넣음
            mean_rating = self.df['rating'].mean()
            fill_value = round(mean_rating) if not pd.isna(mean_rating) else 0
            self.df['rating'] = self.df['rating'].fillna(fill_value).astype(int)
        
        # 4. 'n년전' 형식의 텍스트를 'YYYY-MM-DD'형식으로 변환
        if 'date' in self.df.columns:
            self.df['date'] = self.df['date'].apply(self._convert_relative_date)
            self.df['date'] = pd.to_datetime(self.df['date']).dt.strftime('%Y-%m-%d')
            
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
        # 띄어쓰기 두개 이상의 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _convert_relative_date(self, text):
        """
        'n년 전', 'n개월 전' 등의 텍스트를 실제 날짜로 변환

        Args:
            text (str): 상대적 시간을 나타내는 텍스트.

        Returns:
            pd.Timestamp: 변환된 실제 날짜.
        """
        if pd.isna(text):
            return text
        
        text = str(text)
        # 정규식을 이용해 텍스트에서 숫자만 추출
        match = re.search(r'\d+', text)
        num = int(match.group()) if match else 0
        
        # (base_date)에서 시간만큼 빼서 과거 날짜 도출
        if '년' in text:
            return self.base_date - relativedelta(years=num)
        elif '개월' in text or '달' in text:
            return self.base_date - relativedelta(months=num)
        elif '주' in text:
            return self.base_date - relativedelta(weeks=num)
        elif '일' in text:
            return self.base_date - relativedelta(days=num)
        else:
            return self.base_date

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
        리뷰 길이가 1글자거나 극단적으로 긴 이상치 데이터를 제거.

        Returns:
            pd.DataFrame: 이상치가 제거된 데이터프레임.
        """
        if self.df is not None and 'review_length' in self.df.columns:
            # 하한선: 초성이나 단일 문자 등 의미를 파악할 수 없는 1글자 리뷰 제거
            self.df = self.df[self.df['review_length'] >= 2]
            
        return self.df


    def vectorize_text(self):
        """
        리뷰 텍스트 데이터를 TF-IDF 방식으로 벡터화하고, 생성된 행렬과 벡터라이저를 피클 파일로 저장.

        Returns:
            scipy.sparse.csr_matrix or None: TF-IDF로 변환된 텍스트 Sparse Matrix. 
                                             데이터프레임이 없거나 'review' 컬럼이 존재하지 않으면 None을 반환.
        """
        # 데이터프레임이 정상적으로 로드되어 있고, 'review' 컬럼이 존재하는지 확인
        if self.df is not None and 'review' in self.df.columns:
            
            # 1. TF-IDF 벡터라이저 객체 생성 (빈도수 기준 상위 1000개 단어만 피처로 사용)
            vectorizer = TfidfVectorizer(max_features=1000)
            
            # 2. 리뷰 텍스트 데이터를 학습(fit)하고 동시에 수치형 행렬로 변환(transform)
            tfidf_matrix = vectorizer.fit_transform(self.df['review'])
        
            # 3. 결과물을 저장할 디렉토리가 존재하지 않는다면 새로 생성
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 4. 추후 새로운 데이터 변환이나 모델 학습에 사용하기 위해 벡터라이저와 행렬을 각각 피클(.pkl) 파일로 저장
            joblib.dump(vectorizer, os.path.join(self.output_dir, 'tfidf_vectorizer.pkl'))
            joblib.dump(tfidf_matrix, os.path.join(self.output_dir, 'tfidf_matrix.pkl'))
        
            # 5. 최종적으로 변환된 행렬 데이터를 반환
            return tfidf_matrix

    
    def save_to_database(self):
        """
        최종 전처리된 데이터프레임을 지정된 디렉토리에 CSV 파일로 저장.
        """
        if self.df is not None:
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, 'processed_reviews_GoogleMaps.csv')
            # 엑셀 등에서 한글 깨짐을 방지하기 위해 utf-8-sig 인코딩 사용
            self.df.to_csv(output_file, index=False, encoding='utf-8-sig')