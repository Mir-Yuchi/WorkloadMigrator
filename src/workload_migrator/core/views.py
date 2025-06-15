from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Migration, MigrationTarget, MountPoint, Workload
from .serializers import (
    MigrationSerializer,
    MigrationTargetSerializer,
    MountPointSerializer,
    WorkloadSerializer,
)


class WorkloadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing workloads.
    """

    queryset = Workload.objects.all()
    serializer_class = WorkloadSerializer


class MigrationTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing migration targets.
    """

    queryset = MigrationTarget.objects.all()
    serializer_class = MigrationTargetSerializer


class MigrationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing migrations.
    """

    queryset = Migration.objects.all()
    serializer_class = MigrationSerializer

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """
        Trigger the migration asynchronously via Celery.
        Returns a task ID which can be used for tracking.
        """
        migration = self.get_object()
        from core.tasks import run_migration

        result = run_migration.delay(migration.id, simulated_minutes=0)
        migration.refresh_from_db()
        return Response(
            {"task_id": result.id, "status": migration.state},
            status=status.HTTP_202_ACCEPTED,
        )


class MountPointViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for MountPoint objects.
    """

    queryset = MountPoint.objects.all()
    serializer_class = MountPointSerializer
