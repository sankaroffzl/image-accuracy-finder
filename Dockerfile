FROM python:3.12-slim

RUN apt-get update -qq && apt-get install -y -qq \
    libgl1 libglib2.0-0 \
    > /dev/null 2>&1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ./start.sh
