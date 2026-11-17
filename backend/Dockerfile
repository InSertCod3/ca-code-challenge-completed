FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -r /tmp/requirements.txt && pip install --no-cache-dir --no-deps /app/shared
COPY backend/ /app/
RUN mkdir -p /app/static && python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn","siteconfig.wsgi:application","--bind","0.0.0.0:8000","--workers","2"]
