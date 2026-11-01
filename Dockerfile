FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py content.py ./
RUN useradd --create-home botuser
USER botuser
CMD ["python", "bot.py"]
