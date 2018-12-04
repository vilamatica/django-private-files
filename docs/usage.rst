Usage
=========

Limiting Access to Static Files
----------------------------------

To protect a static file that you have reference to in the database you need
to use the ``PrivateFileField`` model field. For example::

		from django.db import models
		from private_files import PrivateFileField

		class FileSubmission(models.Model):
		    description = models.CharField("description", max_length = 200)
		    uploaded_file = PrivateFileField("file", upload_to = 'uploads')

By default it will check if the user is authenticated and let them download the
file as an attachment.

If you want to do more complex checks for the permission to download the file you
need to pass your own callable to the ``condition`` parameter::

		from django.db import models
		from django.contrib.auth.models import User
		from private_files import PrivateFileField

		def is_owner(request, instance):
		    return (not request.user.is_anonymous()) and request.user.is_authenticated and
				   instance.owner.pk = request.user.pk

		class FileSubmission(models.Model):
		    description = models.CharField("description", max_length = 200)
			owner = models.ForeignKey(User)
		    uploaded_file = PrivateFileField("file", upload_to = 'uploads', condition = is_owner)

This would check if the user requesting the file is the same user referenced in the ``owner`` field and
serve the file if it's true, otherwise it will throw ``PermissionDenied``.
``condition`` should return ``True`` if the ``request`` user should be able to download the file and ``False`` otherwise.

Another optional parameter is ``attachment``. It allows you to control wether the ``content-disposition`` header is sent or not.
By default it is ``True``, meaning the user will always be prompted to download the file by the browser.


Monitoring Access to Static Files
------------------------------------------

By using ``django-private-files`` you can monitor when a file is requested for download.
By hooking to the ``pre_download`` signal. This fires when a user is granted access to a file
and right before the server starts streaming the file to the user. The following is a simple
example of using the signal to provide a download counter::

    from django.db import models
    from django.contrib.auth.models import User
    from private_files import PrivateFileField, pre_download

    class CountedDownloads(models.Model):
        description = models.CharField("description", max_length = 200)
        downloadable = PrivateFileField("file", upload_to = 'downloadables')
        downloads = models.PositiveIntegerField("downloads total", default = 0)

    def handle_pre_download(instance, field_name, request, **kwargs):
        instance.downloads += 1
        instance.save()

    pre_download.connect(handle_pre_download, sender = CountedDownloads)


Working with Amazon S3
------------------------------------------

For managing files in Amazon S3 it is needed install the following dependences::

django-storages::

    pip install django-storages

You need configure folling django settings:

* AWS_STORAGE_BUCKET_NAME: Your Amazon Web Services storage bucket name, as a string.

* AWS_ACCESS_KEY_ID: Your Amazon Web Services access key, as a string.

* AWS_SECRET_ACCESS_KEY: Your Amazon Web Services secret access key, as a string.


More info at https://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html

boto::

    pip install boto

You need configure folling django settings:

* AWS_EXPIRES_IN: How long the url is valid for, in seconds. Default value = 60

More into at http://docs.pythonboto.org/en/latest/


