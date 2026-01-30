FROM python:3.11-slim

WORKDIR /bot

COPY requirements.lock ./requirements.lock
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY src ./src
COPY main.py ./main.py

CMD [ "python3", "main.py" ]