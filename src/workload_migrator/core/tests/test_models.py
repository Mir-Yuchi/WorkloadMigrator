import time

import pytest
from core.models import Credentials, Migration, MigrationTarget, MountPoint, Workload
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestCredentialsModel:
    def test_missing_username(self):
        cred = Credentials(password="pass", domain="d")
        with pytest.raises(ValidationError):
            cred.full_clean()

    def test_missing_password(self):
        cred = Credentials(username="u", domain="d")
        with pytest.raises(ValidationError):
            cred.full_clean()

    def test_missing_domain(self):
        cred = Credentials(username="u", password="p")
        with pytest.raises(ValidationError):
            cred.full_clean()

    def test_valid(self):
        cred = Credentials(username="u", password="p", domain="d")
        cred.full_clean()
        cred.save()
        assert Credentials.objects.count() == 1


@pytest.mark.django_db
class TestWorkloadModel:
    def test_ip_unique(self):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        w1 = Workload.objects.create(ip="192.0.2.1", credentials=c)
        with pytest.raises(ValidationError):
            w2 = Workload(ip="192.0.2.1", credentials=c)
            w2.full_clean()

    def test_ip_immutable(self):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        w = Workload.objects.create(ip="192.0.2.2", credentials=c)
        w.ip = "192.0.2.3"
        with pytest.raises(ValueError):
            w.save()

    def test_mountpoint_relation(self):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        w = Workload.objects.create(ip="192.0.2.4", credentials=c)
        m = MountPoint.objects.create(
            workload=w, mount_point_name="D:\\", total_size=100
        )
        assert w.mountpoints.count() == 1
        assert w.mountpoints.first() == m


@pytest.mark.django_db
class TestMigrationTargetModel:
    def test_invalid_cloud_type(self):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        w = Workload.objects.create(ip="192.0.2.5", credentials=c)
        with pytest.raises(ValidationError):
            tgt = MigrationTarget(
                cloud_type="gcp", cloud_credentials=c, target_vm=w  # invalid
            )
            tgt.full_clean()

    def test_valid_cloud_types(self):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        w = Workload.objects.create(ip="192.0.2.6", credentials=c)
        for ct in ["aws", "azure", "vsphere", "vcloud"]:
            tgt = MigrationTarget(cloud_type=ct, cloud_credentials=c, target_vm=w)
            tgt.full_clean()  # should not raise
            tgt.save()
        assert MigrationTarget.objects.count() == 4


@pytest.mark.django_db
class TestMigrationModel:
    def test_run_disallows_c_root(self, monkeypatch):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        src = Workload.objects.create(ip="192.0.2.7", credentials=c)
        mp_c = MountPoint.objects.create(
            workload=src, mount_point_name="C:\\", total_size=50
        )
        mp_d = MountPoint.objects.create(
            workload=src, mount_point_name="D:\\", total_size=75
        )
        tgt = MigrationTarget.objects.create(
            cloud_type="aws",
            cloud_credentials=c,
            target_vm=Workload.objects.create(ip="192.0.2.8", credentials=c),
        )
        mig = Migration.objects.create(source=src, migration_target=tgt)
        mig.selected_mountpoints.set([mp_c, mp_d])

        with pytest.raises(ValidationError):
            mig.run(simulated_minutes=0)  # immediate run

    def test_run_copies_only_selected(self, monkeypatch):
        c = Credentials.objects.create(username="u", password="p", domain="d")
        src = Workload.objects.create(ip="192.0.2.9", credentials=c)
        mp1 = MountPoint.objects.create(
            workload=src, mount_point_name="X:\\", total_size=20
        )
        mp2 = MountPoint.objects.create(
            workload=src, mount_point_name="Y:\\", total_size=30
        )
        tgt_vm = Workload.objects.create(ip="192.0.2.10", credentials=c)
        tgt = MigrationTarget.objects.create(
            cloud_type="azure", cloud_credentials=c, target_vm=tgt_vm
        )
        mig = Migration.objects.create(source=src, migration_target=tgt)
        mig.selected_mountpoints.set([mp2])

        # Patch sleep to avoid delay
        monkeypatch.setattr(time, "sleep", lambda s: None)
        mig.run(simulated_minutes=0)

        # After run, target_vm should have only the selected mountpoint
        mps = list(tgt_vm.mountpoints.all())
        assert len(mps) == 1
        assert mps[0].mount_point_name == "Y:\\"
        assert mig.state == Migration.State.SUCCESS
