from django.core.files.storage import get_storage_class
from storages.backends.s3boto import S3BotoStorage
from django.conf import settings
from dateutil import tz


class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            'compressor.storage.CompressorFileStorage')()

    def save(self, name, content):
        name = super(CachedS3BotoStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name

    def modified_time(self, prefixed_path):
        # S3BotoStorage returns a UTC timestamp (which it gets from S3)
        # but an offset-naive one.
        # collectstatic needs to compare that timestamp against
        # a local timestamp (but again an offset-naive one)
        # so here, we need to convert our naive UTC to a naive local
        # takes a few steps...

        # get the offset-naive UTC timestamp
        r = super(CachedS3BotoStorage, self).modified_time(prefixed_path)

        # make it offset-aware
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(settings.TIME_ZONE)
        utc = r.replace(tzinfo=from_zone)

        # convert it to a local offset-aware one
        lcl = utc.astimezone(to_zone)

        # then make it offset-naive
        naive = lcl.replace(tzinfo=None)
        return naive


CompressorS3BotoStorage = lambda: CachedS3BotoStorage(location='compressor')
MediaRootS3BotoStorage = lambda: S3BotoStorage(location='media')
