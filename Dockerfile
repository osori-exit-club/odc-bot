# 1. 베이스 이미지 선택
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /

# 3. 필요한 의존성 파일 복사
COPY requirements.txt .

# 4. 필요한 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 봇 코드 복사
COPY . .

# 6. 봇 실행
CMD ["python3", "bot.py"]