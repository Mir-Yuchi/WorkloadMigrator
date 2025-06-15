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
        Run the migration for the specified migration instance.
        """
        migration = self.get_object()
        try:
            migration.run(simulated_minutes=0)
            return Response({"status": migration.state})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MountPointViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for MountPoint objects.
    """

    queryset = MountPoint.objects.all()
    serializer_class = MountPointSerializer
