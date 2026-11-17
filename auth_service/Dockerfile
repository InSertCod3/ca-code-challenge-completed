FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY auth_service/requirements.txt /tmp/requirements.txt
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /tmp/requirements.txt && pip install --no-cache-dir --no-deps /app/shared
COPY auth_service/ /app/
EXPOSE 8000
CMD ["gunicorn","authconfig.wsgi:application","--bind","0.0.0.0:8000","--workers","2"]
