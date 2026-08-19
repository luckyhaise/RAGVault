from celery import Celery
from app.core.config import settings
redis_url = settings.redis_url
celery_app = Celery("ragvault",broker=redis_url,backend=redis_url)

