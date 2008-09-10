from datetime import datetime
from django.db import models

class Entry(models.Model):
    class Meta:
        ordering = ['date_add','name']

    date_add = models.DateTimeField('datum', default=datetime.now(), blank=True)
    ip = models.IPAddressField('IP', blank=True, null=True)
    name = models.CharField('naam', max_length=200)
    email = models.EmailField('e-mail', blank=True, null=True)
    url = models.URLField('website', blank=True, null=True)
    activated = models.BooleanField('geactiveerd', default=True)

    text = models.TextField()
    
    def __unicode__(self):
        return "%s, %s" % (self.name, self.date_add)

