FROM python:3.11-slim
WORKDIR /
COPY requirements-for-server.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "src/bot.py"]