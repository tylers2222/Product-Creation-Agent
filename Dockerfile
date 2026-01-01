FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y redis-server

RUN echo '#!/bin/bash\n\
redis-server --daemonize yes\n\
python3 main.py' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]