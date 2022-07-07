from syntax.models import Release


class ReleaseMixin:
    @property
    def release(self) -> Release:
        release_version = self.request.query_params.get('release_version')  # type: ignore

        if release_version:
            release = Release.objects.filter(release_version=release_version).first()

            if not release:
                raise Exception('Release version not found.')
        else:
            release = Release.get_current_release()

        return release
