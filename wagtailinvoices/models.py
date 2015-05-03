from __future__ import absolute_import, unicode_literals

from six import text_type, string_types

from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from django.utils.text import slugify
from uuidfield import UUIDField


from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import resolve_model_string
from wagtail.wagtailsearch import index


INVOICEINDEX_MODEL_CLASSES = []
_INVOICEINDEX_CONTENT_TYPES = []


def get_invoiceindex_content_types():
    global _INVOICEINDEX_CONTENT_TYPES
    if len(_INVOICEINDEX_CONTENT_TYPES) != len(INVOICEINDEX_MODEL_CLASSES):
        _INVOICEINDEX_CONTENT_TYPES = [
            ContentType.objects.get_for_model(cls)
            for cls in INVOICEINDEX_MODEL_CLASSES]
    return _INVOICEINDEX_CONTENT_TYPES


class InvoiceIndexMixin(RoutablePageMixin):

    class Meta: 
        pass

    invoice_model = None
    subpage_types = []

    subpage_urls = (
        url(r'^(?P<uuid>[0-9a-f-]+)/$', 'v_invoice', name='invoice'),
    )

    v_invoice = lambda s, r, **k: frontend.invoice_detail(r, s, **k)

    @classmethod
    def get_invoice_model(cls):
        if isinstance(cls.invoice_model, models.Model):
            return cls.invoice_model
        elif isinstance(cls.invoice_model, string_types):
            return resolve_model_string(cls.invoice_model, cls._meta.app_label)
        else:
            raise ValueError('Can not resolve {0}.invoice_model in to a model: {1!r}'.format(
                cls.__name__, cls.invoice_model))


class AbstractInvoice(models.Model):

    invoiceindex = models.ForeignKey(Page)
    time = models.DateTimeField('Issue date', default=timezone.now)
    uuid = UUIDField(auto=True, null=True, default=None)

    panels = [
        FieldPanel('time'),
    ]

    search_fields = (index.FilterField('time'),)

    class Meta:
        ordering = ('-time',)
        abstract = True

    def get_nice_url(self):
        return slugify(text_type(self))

    def get_template(self, request):
        try:
            return self.template
        except AttributeError:
            return '{0}/{1}.html'.format(self._meta.app_label, self._meta.model_name)

    def url(self):
        invoiceindex = self.invoiceindex.specific
        url = invoiceindex.url + invoiceindex.reverse_subpage('invoice', kwargs={
            'uuid': str(self.uuid)})
        return url

    def serve(self, request):
        return render(request, self.get_template(request), {
            'self': self.invoiceindex.specific,
            'invoice': self,
        })


# Need to import this down here to prevent circular imports :(
from .views import frontend