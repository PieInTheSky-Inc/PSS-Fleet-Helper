FROM python:3.11-slim

WORKDIR /bot

COPY requirements.txt ./
RUN PYTHONDONTWRITEBYTECODE=1 pip3 install --no-cache-dir -r requirements.txt

COPY src ./src
COPY main.py ./main.py

CMD [ "python3", "main.py" ]