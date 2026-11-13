FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && \
    useradd --system --gid app --home-dir /app app && \
    mkdir -p /data /app/staticfiles && \
    chown -R app:app /data /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

USER app
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile - --timeout 60 portfolio_site.wsgi:application"]
