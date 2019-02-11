import os
import uuid
import logging
from django import get_version as get_django_version
from django.db.models.fields.files import FileField, ImageField, ImageFieldFile, FieldFile
from django.conf import settings
from django.core.files.storage import default_storage

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy

try:
    from boto.s3.connection import S3Connection
except ImportError:
    S3Connection = None


log = logging.getLogger(__name__)


PROTECTION_METHODS = ['basic', 'nginx', 'lighttpd', 'apache']


class PrivateFieldFile(FieldFile):
    def _get_url(self):
        self._require_file()
        app_label = self.instance._meta.app_label
        model_name = self.instance._meta.object_name.lower()
        field_name = self.field.name
        pk = self.instance.pk
        if hasattr(settings, "AWS_STORAGE_BUCKET_NAME") and settings.AWS_STORAGE_BUCKET_NAME:
            # Tested with django-2.1.2 and django-storages 1.6.6 and boto==2.49.0
            if S3Connection:
                aws_expires_in = 60
                if hasattr(settings, "AWS_EXPIRES_IN") and settings.AWS_EXPIRES_IN:
                    try:
                        aws_expires_in = int(settings.AWS_EXPIRES_IN)
                    except (TypeError, ValueError):
                        pass

                ar_django = get_django_version().split(".")
                if int(ar_django[0]) >= 1:
                    storage = u"%s" % default_storage.connection
                    if storage.split(":")[0].upper() == u"S3CONNECTION":
                        try:
                            s3 = S3Connection(settings.AWS_ACCESS_KEY_ID,
                                              settings.AWS_SECRET_ACCESS_KEY)
                            filename = s3.generate_url(aws_expires_in, 'GET',
                                                       bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                                       key=self.file)
                            return filename
                        except Exception as e:
                            log.warning("%s" % e)
            else:
                log.warning("Please, install boto in order to access to Amazon AWS S3 buckets")
        filename = os.path.basename(self.path)
        url = reverse_lazy('private_files-file', args=[app_label, model_name, field_name, pk, filename])
        if self.field.single_use:
            from django.core.cache import cache
            access_key = uuid.uuid4().hex
            cache.set(access_key, '%s-%s-%s-%s-%s' % (app_label, model_name, field_name, pk, filename), 3600)
            url += '?access-key=' + access_key
        return url

    url = property(_get_url)

    def _get_contidion(self):
        return self.field.condition
    condition = property(_get_contidion)

    def _get_attachment(self):
        return self.field.attachment
    attachment = property(_get_attachment)

    def _get_single_use(self):
        return self.field.single_use
    single_use = property(_get_single_use)


def is_user_authenticated(request, instance):
    return (not request.user.is_anonymous) and request.user.is_authenticated


class PrivateFileField(FileField):
    attr_class = PrivateFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, condition=is_user_authenticated,
                 attachment=True, single_use=False, **kwargs):
        super(PrivateFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)
        self.condition = condition
        self.attachment = attachment
        self.single_use = single_use
