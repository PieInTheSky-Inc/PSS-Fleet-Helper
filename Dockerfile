FROM python:3.11-slim

WORKDIR /bot

COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip3 install --no-cache-dir -r requirements.lock

COPY src ./src
COPY main.py ./main.py

CMD [ "python3", "main.py" ]