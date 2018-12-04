import os

from django.db.models.fields.files import FileField, ImageField, ImageFieldFile, FieldFile
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.conf import settings

PROTECTION_METHODS = ['basic', 'nginx', 'lighttpd', 'apache']

class PrivateFieldFile(FieldFile):
    def _get_url(self):
        self._require_file()
        app_label = self.instance._meta.app_label
        model_name  = self.instance._meta.object_name.lower()
        field_name = self.field.name
        pk = self.instance.pk
        if hasattr(settings, "AWS_STORAGE_BUCKET_NAME"):
            """
            Tested with django-1.5.1 and django-storages 1.1.8 and boto==2.34.0

            @TODO Fixit with django-1.2
            """
            try:
                import django
                if hasattr(settings, "AWS_EXPIRES_IN"):
                    aws_expires_in = settings.AWS_EXPIRES_IN
                else:
                    aws_expires_in = 60
                ar_django = django.get_version().split(".")
                if int(ar_django[0]) == 1:
                    if int(ar_django[1]) >= 3:
                        storage = u"%s" % default_storage.connection
                    else:
                        storage = ""
                    if storage.split(":")[0].upper() == u"S3CONNECTION":
                        from boto.s3.connection import S3Connection
                        s3 = S3Connection(settings.AWS_ACCESS_KEY_ID,
                                          settings.AWS_SECRET_ACCESS_KEY)
                        filename = s3.generate_url(aws_expires_in, 'GET',
                                            bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                            key=self.file)
                        return filename
            except:
                pass
        filename = os.path.basename(self.path)
        return reverse('private_files-file', args=[app_label, model_name, field_name, pk, filename])


    url = property(_get_url)

    def _get_contidion(self):
        return self.field.condition

    condition = property(_get_contidion)

    def _get_attachment(self):
        return self.field.attachment

    attachment = property(_get_attachment)



def is_user_authenticated(request, instance):
    return (not request.user.is_anonymous()) and request.user.is_authenticated

class PrivateFileField(FileField):
    attr_class = PrivateFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, condition = is_user_authenticated, attachment = True, **kwargs):
        super(PrivateFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)
        self.condition = condition
        self.attachment = attachment
