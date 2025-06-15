import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_full_migration_flow(client):
    # 1) Create Workload
    wl_resp = client.post(
        reverse("workload-list"),
        {
            "ip": "192.0.2.150",
            "credentials": {
                "username": "apiuser",
                "password": "apipass",
                "domain": "apidomain",
            },
        },
        format="json",
    )
    assert wl_resp.status_code == 201
    wl_id = wl_resp.data["id"]

    # 2) Create MountPoints
    mp1 = client.post(
        reverse("mountpoint-list"),
        {"workload": wl_id, "mount_point_name": "X:\\", "total_size": 10},
        format="json",
    )
    mp2 = client.post(
        reverse("mountpoint-list"),
        {"workload": wl_id, "mount_point_name": "Y:\\", "total_size": 20},
        format="json",
    )
    assert mp1.status_code == 201
    assert mp2.status_code == 201

    # 3) Create a MigrationTarget
    mt_resp = client.post(
        reverse("migrationtarget-list"),
        {
            "cloud_type": "aws",
            "cloud_credentials": {
                "username": "apiuser",
                "password": "apipass",
                "domain": "apidomain",
            },
            "target_vm": wl_id,
        },
        format="json",
    )
    assert mt_resp.status_code == 201
    mt_id = mt_resp.data["id"]

    # 4) Create Migration
    mig_resp = client.post(
        reverse("migration-list"),
        {
            "source": wl_id,
            "migration_target": mt_id,
            "selected_mountpoints": [mp1.data["id"], mp2.data["id"]],
        },
        format="json",
    )
    assert mig_resp.status_code == 201
    mig_id = mig_resp.data["id"]

    # 5) Run Migration
    run_resp = client.post(reverse("migration-run", args=[mig_id]), format="json")
    assert run_resp.status_code == 202
    assert "task_id" in run_resp.data
    returned_status = run_resp.data["status"]
    assert returned_status in ("success", "error")

    # 6) Check final state
    status_resp = client.get(reverse("migration-detail", args=[mig_id]), format="json")
    assert status_resp.status_code == 200
    assert status_resp.data["state"] == returned_status
