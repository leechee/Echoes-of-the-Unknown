FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/ data/

ARG ENTRYPOINT=src/api.py
ENV ENTRYPOINT=${ENTRYPOINT}
CMD ["sh", "-c", "python $ENTRYPOINT"]
