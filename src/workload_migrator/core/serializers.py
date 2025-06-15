from rest_framework import serializers

from .models import Credentials, Migration, MigrationTarget, MountPoint, Workload


class CredentialsSerializer(serializers.ModelSerializer):
    """
    Serializer for Credentials model.
    """

    class Meta:
        model = Credentials
        fields = ["id", "username", "password", "domain"]


class MountPointSerializer(serializers.ModelSerializer):
    """
    Serializer for MountPoint model.
    """

    class Meta:
        model = MountPoint
        fields = ["id", "mount_point_name", "total_size"]


class WorkloadSerializer(serializers.ModelSerializer):
    """
    Serializer for Workload model.
    """

    credentials = CredentialsSerializer()
    mountpoints = MountPointSerializer(many=True, read_only=True)

    class Meta:
        model = Workload
        fields = ["id", "ip", "credentials", "mountpoints"]

    def create(self, validated_data):
        creds_data = validated_data.pop("credentials")
        creds = Credentials.objects.create(**creds_data)
        return Workload.objects.create(credentials=creds, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("ip", None)
        return super().update(instance, validated_data)


class MigrationTargetSerializer(serializers.ModelSerializer):
    """
    Serializer for MigrationTarget model.
    """

    cloud_credentials = CredentialsSerializer()
    target_vm = serializers.PrimaryKeyRelatedField(queryset=Workload.objects.all())

    class Meta:
        model = MigrationTarget
        fields = ["id", "cloud_type", "cloud_credentials", "target_vm"]

    def create(self, validated_data):
        creds_data = validated_data.pop("cloud_credentials")
        creds = Credentials.objects.create(**creds_data)
        return MigrationTarget.objects.create(cloud_credentials=creds, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("target_vm", None)
        creds_data = validated_data.pop("cloud_credentials", None)
        if creds_data:
            creds = instance.cloud_credentials
            for attr, value in creds_data.items():
                setattr(creds, attr, value)
            creds.save()
        return super().update(instance, validated_data)


class MigrationSerializer(serializers.ModelSerializer):
    """
    Serializer for Migration model.
    """

    selected_mountpoints = serializers.PrimaryKeyRelatedField(
        many=True, queryset=MountPoint.objects.all()
    )

    class Meta:
        model = Migration
        fields = ["id", "source", "migration_target", "selected_mountpoints", "state"]
        read_only_fields = ["state"]
