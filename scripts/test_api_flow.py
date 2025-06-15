#!/usr/bin/env python3
"""
Test harness for the WorkloadMigrator REST API.
"""

import requests

API = "http://localhost:8000/api"


def create_workload(ip, username, password, domain):
    r = requests.post(
        f"{API}/workloads/",
        json={
            "ip": ip,
            "credentials": {
                "username": username,
                "password": password,
                "domain": domain,
            },
        },
    )
    r.raise_for_status()
    return r.json()["id"]


def create_mountpoint(wl_id, name, size):
    r = requests.post(
        f"{API}/mountpoints/",
        json={
            "workload": wl_id,
            "mount_point_name": name,
            "total_size": size,
        },
    )
    r.raise_for_status()
    return r.json()["id"]


def create_target(wl_id, username, password, domain, cloud_type="aws"):
    r = requests.post(
        f"{API}/targets/",
        json={
            "cloud_type": cloud_type,
            "cloud_credentials": {
                "username": username,
                "password": password,
                "domain": domain,
            },
            "target_vm": wl_id,
        },
    )
    r.raise_for_status()
    return r.json()["id"]


def create_migration(src_id, tgt_id, mps):
    r = requests.post(
        f"{API}/migrations/",
        json={
            "source": src_id,
            "migration_target": tgt_id,
            "selected_mountpoints": mps,
        },
    )
    r.raise_for_status()
    return r.json()["id"]


def run_migration(mig_id):
    r = requests.post(f"{API}/migrations/{mig_id}/run/")
    r.raise_for_status()
    data = r.json()
    print("Run dispatched:", data)
    return data["status"]


if __name__ == "__main__":
    print("Starting local REST API flow test...")
    wl = create_workload("192.0.2.250", "localuser", "localpass", "localdom")
    print("Workload ID:", wl)
    mp1 = create_mountpoint(wl, "X:\\", 10)
    mp2 = create_mountpoint(wl, "Y:\\", 20)
    print("MountPoints:", mp1, mp2)
    tgt = create_target(wl, "localuser", "localpass", "localdom")
    print("Target ID:", tgt)
    mig = create_migration(wl, tgt, [mp1, mp2])
    print("Migration ID:", mig)
    status = run_migration(mig)
    print("Final migration status:", status)
