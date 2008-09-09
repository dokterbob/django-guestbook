from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from models import Entry

class EntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_add', 'activated')
    
admin.site.register(Entry, EntryAdmin)