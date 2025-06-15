from celery import shared_task
from core.models import Migration
from django.core.exceptions import ObjectDoesNotExist


@shared_task(bind=True)
def run_migration(self, migration_id: int, simulated_minutes: int = 1):
    """
    Celery task to perform a Migration asynchronously by delegating
    to the model's run() method. Retries on failure.
    :param self:
    :param migration_id:
    :param simulated_minutes:
    :return: None
    """
    try:
        migration = Migration.objects.get(pk=migration_id)
    except ObjectDoesNotExist:
        raise

    try:
        migration.run(simulated_minutes=simulated_minutes)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
