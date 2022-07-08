from rest_framework import serializers

from .models import Release, ReleaseChange


class ReleaseSerializer(serializers.ModelSerializer):
    unapplied_changes = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = [
            'id',
            'release_version',
            'release_notes',
            'released_at',
            'released_by',
            'current_release',
            'parent',
            'unapplied_changes',
        ]
        extra_kwargs = {
            'released_by': {'read_only': True},
            'current_release': {'read_only': True},
            'parent': {'read_only': True},
        }

    def get_unapplied_changes(self, obj):
        return obj.release_changes.count()

    def validate(self, data):
        """
        Validate that there are ReleaseChanges made for the current Release.
        """
        current_release = Release.get_current_release()

        if not current_release.release_changes.all().exists():
            raise serializers.ValidationError(
                'There have been no changes made to the current release.'
            )

        return data

    def create(self, validated_data):
        current_release = Release.get_current_release()

        return Release.objects.create(
            parent=current_release,
            release_version=validated_data['release_version'],
            release_notes=validated_data['release_notes'],
            released_by=self.context['request'].user,
        )


class ReleaseChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseChange
        fields = [
            'change_type',
            'model_type',
            'syntax_json',
            'created_at',
        ]
