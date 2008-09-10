from django.conf.urls.defaults import *

from django.views.generic.list_detail import object_list

#from views import *

from models import Entry

list_dict = { 'queryset' : Entry.objects.filter(activated=True),
              'paginate_by' : 5,
              'allow_empty' : False,
              'template_object_name' : 'entry' }

urlpatterns = patterns('',
    (r'^$', object_list, dict(list_dict), {'page':'last'}),
    (r'^page(?P<page>[0-9]+)/$', object_list, dict(list_dict)),
    (r'^post/', post_entry),
)

