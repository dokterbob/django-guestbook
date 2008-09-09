from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
     (r'^$', last_page),
     (r'^add/', add_entry),
     (r'^(?P<page>[0-9]+)/$', guestbook_list),
)

