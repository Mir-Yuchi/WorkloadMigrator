import time

from django.core.exceptions import ValidationError
from django.db import models


class Credentials(models.Model):
    """
    Stores credentials for accessing a workload or cloud.
    All fields are required.
    """

    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    domain = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.username}@{self.domain}"


class Workload(models.Model):
    """
    Represents a VM or workload with an immutable IP and associated credentials.
    """

    ip = models.GenericIPAddressField(unique=True)
    credentials = models.ForeignKey(
        Credentials,
        on_delete=models.CASCADE,
        related_name="workloads",
    )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Workload.objects.get(pk=self.pk)
            if orig.ip != self.ip:
                raise ValueError("IP address cannot be changed once set.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Workload(ip={self.ip})"


class MountPoint(models.Model):
    """
    A storage mount point on a workload.
    """

    workload = models.ForeignKey(
        Workload,
        on_delete=models.CASCADE,
        related_name="mountpoints",
    )
    mount_point_name = models.CharField(max_length=10)
    total_size = models.PositiveIntegerField(help_text="Total size in GB")

    def __str__(self):
        return f"{self.workload.ip}:{self.mount_point_name} ({self.total_size}GB)"


class MigrationTarget(models.Model):
    """
    Specifies the target environment and VM for a migration.
    """

    CLOUD_CHOICES = [
        ("aws", "AWS"),
        ("azure", "Azure"),
        ("vsphere", "vSphere"),
        ("vcloud", "vCloud"),
    ]

    cloud_type = models.CharField(
        max_length=20,
        choices=CLOUD_CHOICES,
    )
    cloud_credentials = models.ForeignKey(
        Credentials,
        on_delete=models.CASCADE,
        related_name="cloud_target_credentials",
    )
    target_vm = models.ForeignKey(
        Workload,
        on_delete=models.CASCADE,
        related_name="as_migration_target",
    )

    def clean(self):
        if self.cloud_type not in dict(self.CLOUD_CHOICES):
            raise ValidationError(f"Invalid cloud_type: {self.cloud_type}")

    def __str__(self):
        return f"MigrationTarget({self.cloud_type} -> {self.target_vm.ip})"


class Migration(models.Model):
    """
    Represents a migration from a source workload to a MigrationTarget,
    moving only selected mount points.
    """

    class State(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        RUNNING = "running", "Running"
        ERROR = "error", "Error"
        SUCCESS = "success", "Success"

    source = models.ForeignKey(
        Workload,
        on_delete=models.CASCADE,
        related_name="migrations",
    )
    migration_target = models.ForeignKey(
        MigrationTarget,
        on_delete=models.CASCADE,
        related_name="migrations",
    )
    selected_mountpoints = models.ManyToManyField(
        MountPoint,
        related_name="+",
    )
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.NOT_STARTED,
    )

    def run(self, simulated_minutes: int = 1):
        """
        Execute the migration:
        - Disallow if 'C:\\' is selected
        - Mark as running
        - Sleep to simulate transfer
        - Copy selected mount points onto the target VM
        - Update state to SUCCESS or ERROR
        """
        if self.selected_mountpoints.filter(mount_point_name__iexact="C:\\").exists():
            raise ValidationError("Migrations including C:\\ are not allowed.")

        self.state = self.State.RUNNING
        self.save()

        try:
            time.sleep(simulated_minutes * 60)

            target_vm = self.migration_target.target_vm
            target_vm.mountpoints.all().delete()

            for mp in self.selected_mountpoints.all():
                MountPoint.objects.create(
                    workload=target_vm,
                    mount_point_name=mp.mount_point_name,
                    total_size=mp.total_size,
                )

            self.state = self.State.SUCCESS
            self.save()

        except Exception:
            self.state = self.State.ERROR
            self.save()
            raise

    def __str__(self):
        return f"Migration({self.source.ip} → {self.migration_target.cloud_type}/{self.migration_target.target_vm.ip})"
