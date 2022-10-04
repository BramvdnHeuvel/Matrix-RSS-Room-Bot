FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY update.py ./
RUN python update.py

COPY src/ ./src/
COPY main.py ./

ENV CONFIG_FILE=/config.yml

CMD ["python", "main.py"]