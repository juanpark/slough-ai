web: PYTHONPATH=. python src/app.py
worker: PYTHONPATH=. celery -A src.worker worker --loglevel=info
beat: PYTHONPATH=. celery -A src.worker beat --loglevel=info
