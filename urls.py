from django.conf.urls.defaults import *
from models import *

urlpatterns = patterns('amfibi.guestbook.views',
     (r'^$', 'last_page'),
     (r'^add/', 'add_entry'),
     (r'^(?P<page>[0-9]+)/$', 'guestbook_list'),
)

