import time

from django.core.exceptions import ValidationError
from django.db import models


class Credentials(models.Model):
    """
    Represents credentials for accessing a workload or cloud service.
    """

    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    domain = models.CharField(max_length=150)

    def __str__(self):
        return f"Credentials(username={self.username}, domain={self.domain})"


class Workload(models.Model):
    """
    Represents a workload with an IP address and associated credentials.
    """

    ip = models.GenericIPAddressField(unique=True)
    credentials = models.OneToOneField(
        Credentials, on_delete=models.CASCADE, related_name="workload"
    )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Workload.objects.get(pk=self.pk)
            if orig.ip != self.ip:
                raise ValidationError("IP address cannot be changed once set.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Workload(ip={self.ip})"


class MountPoint(models.Model):
    """
    Represents a mount point on a workload, such as a disk or volume.
    """

    workload = models.ForeignKey(
        Workload, on_delete=models.CASCADE, related_name="mount_points"
    )
    mount_point_name = models.CharField(max_length=32)
    total_size = models.PositiveIntegerField()

    class Meta:
        unique_together = ("workload", "mount_point_name")

    def __str__(self):
        return f"MountPoint({self.mount_point_name} on {self.workload.ip})"


class MigrationTarget(models.Model):
    """
    Represents a target for migration, which can be a cloud service or another workload.
    """

    CLOUD_AWS = "aws"
    CLOUD_AZURE = "azure"
    CLOUD_VSPHERE = "vsphere"
    CLOUD_VCLOUD = "vcloud"
    CLOUD_CHOICES = [
        (CLOUD_AWS, "AWS"),
        (CLOUD_AZURE, "Azure"),
        (CLOUD_VSPHERE, "vSphere"),
        (CLOUD_VCLOUD, "vCloud"),
    ]

    cloud_type = models.CharField(max_length=16, choices=CLOUD_CHOICES)
    cloud_credentials = models.ForeignKey(
        Credentials, on_delete=models.CASCADE, related_name="cloud_targets"
    )
    target_vm = models.ForeignKey(
        Workload, on_delete=models.CASCADE, related_name="as_target"
    )

    def __str__(self):
        return f"MigrationTarget(type={self.cloud_type}, vm={self.target_vm.ip})"


class Migration(models.Model):
    """
    Represents a migration operation from one workload to another.
    """

    STATE_NOT_STARTED = "not_started"
    STATE_RUNNING = "running"
    STATE_ERROR = "error"
    STATE_SUCCESS = "success"
    STATE_CHOICES = [
        (STATE_NOT_STARTED, "Not Started"),
        (STATE_RUNNING, "Running"),
        (STATE_ERROR, "Error"),
        (STATE_SUCCESS, "Success"),
    ]

    selected_mountpoints = models.ManyToManyField(MountPoint, related_name="migrations")
    source = models.ForeignKey(
        Workload, on_delete=models.CASCADE, related_name="migrations"
    )
    migration_target = models.ForeignKey(
        MigrationTarget, on_delete=models.CASCADE, related_name="migrations"
    )
    state = models.CharField(
        max_length=16, choices=STATE_CHOICES, default=STATE_NOT_STARTED
    )

    def run(self, minutes: int = 1):
        # cannot run if C:\ is selected
        if self.selected_mountpoints.filter(mount_point_name__iexact="C:\\").exists():
            raise ValidationError("Migration cannot include C:\\ volume.")

        self.state = self.STATE_RUNNING
        self.save()

        try:
            time.sleep(minutes * 60)
            target_vm = self.migration_target.target_vm
            target_vm.mount_points.all().delete()

            for mp in self.selected_mountpoints.all():
                MountPoint.objects.create(
                    workload=target_vm,
                    mount_point_name=mp.mount_point_name,
                    total_size=mp.total_size,
                )

            self.state = self.STATE_SUCCESS
        except Exception:
            self.state = self.STATE_ERROR
        finally:
            self.save()

    def __str__(self):
        return f"Migration(source={self.source.ip}, target={self.migration_target}, state={self.state})"
