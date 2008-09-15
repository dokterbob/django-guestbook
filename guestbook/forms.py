import re
import time
import datetime

from django import forms
from django.forms.util import ErrorDict
from django.conf import settings
from django.http import Http404
from django.utils.encoding import force_unicode
from django.utils.hashcompat import sha_constructor
from django.utils.text import get_text_list
from django.utils.translation import ngettext
from django.utils.translation import ugettext_lazy as _

from models import Entry

GUESTBOOK_ENTRY_MAX_LENGTH = getattr(settings,'GUESTBOOK_ENTRY_MAX_LENGTH', 3000)

class EntryForm(forms.Form):
    name          = forms.CharField(label=_("Name"), max_length=50)
    email         = forms.EmailField(label=_("Email address"))
    url           = forms.URLField(label=_("URL"), required=False)
    text       = forms.CharField(label=_('Comment'), widget=forms.Textarea,
                                    max_length=GUESTBOOK_ENTRY_MAX_LENGTH)
    honeypot      = forms.CharField(required=False,
                                    label=_('If you enter anything in this field '\
                                            'your text will be treated as spam'))
    
    timestamp     = forms.IntegerField(widget=forms.HiddenInput)
    security_hash = forms.CharField(min_length=40, max_length=40, widget=forms.HiddenInput)

    def __init__(self, data=None, initial=None):
        if initial is None:
            initial = {}
        initial.update(self.generate_security_data())
        super(EntryForm, self).__init__(data=data, initial=initial)

    def get_entry_object(self):
        """
        Return a new (unsaved) comment object based on the information in this
        form. Assumes that the form is already validated and will throw a
        ValueError if not.

        Does not set any of the fields that would come from a Request object
        (i.e. ``user`` or ``ip_address``).
        """
        if not self.is_valid():
            raise ValueError("get_entry_object may only be called on valid forms")

        new = Entry(
            name    = self.cleaned_data["name"],
            email   = self.cleaned_data["email"],
            url     = self.cleaned_data["url"],
            text      = self.cleaned_data["text"],
            submit_date  = datetime.datetime.now(),
            site_id      = settings.SITE_ID,
            is_removed   = False,
        )

        # Check that this comment isn't duplicate. (Sometimes people post comments
        # twice by mistake.) If it is, fail silently by returning the old comment.
        possible_duplicates = Entry.objects.filter(
            name = new.name,
            email = new.email,
            url = new.url,
        )
        for old in possible_duplicates:
            if old.submit_date.date() == new.submit_date.date() and old.text == new.text:
                return old

        return new

    def security_errors(self):
        """Return just those errors associated with security"""
        errors = ErrorDict()
        for f in ["honeypot", "timestamp", "security_hash"]:
            if f in self.errors:
                errors[f] = self.errors[f]
        return errors

    def clean_honeypot(self):
        """Check that nothing's been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]
        if value:
            raise forms.ValidationError(self.fields["honeypot"].label)
        return value

    def clean_security_hash(self):
        """Check the security hash."""
        security_hash_dict = {
            'timestamp' : self.data.get("timestamp", ""),
        }
        expected_hash = self.generate_security_hash(**security_hash_dict)
        actual_hash = self.cleaned_data["security_hash"]
        if expected_hash != actual_hash:
            raise forms.ValidationError("Security hash check failed.")
        return actual_hash

    def clean_timestamp(self):
        """Make sure the timestamp isn't too far (> 2 hours) in the past."""
        ts = self.cleaned_data["timestamp"]
        if time.time() - ts > (2 * 60 * 60):
            raise forms.ValidationError("Timestamp check failed")
        return ts

    def clean_text(self):
        """
        If COMMENTS_ALLOW_PROFANITIES is False, check that the comment doesn't
        contain anything in PROFANITIES_LIST.
        """
        text = self.cleaned_data["text"]
        if settings.COMMENTS_ALLOW_PROFANITIES == False:
            bad_words = [w for w in settings.PROFANITIES_LIST if w in text.lower()]
            if bad_words:
                plural = len(bad_words) > 1
                raise forms.ValidationError(ngettext(
                    "Watch your mouth! The word %s is not allowed here.",
                    "Watch your mouth! The words %s are not allowed here.", plural) % \
                    get_text_list(['"%s%s%s"' % (i[0], '-'*(len(i)-2), i[-1]) for i in bad_words], 'and'))
        return text

    def generate_security_data(self):
        """Generate a dict of security data for "initial" data."""
        timestamp = int(time.time())
        security_dict =   {
            'timestamp'     : str(timestamp),
            'security_hash' : self.initial_security_hash(timestamp),
        }
        return security_dict

    def initial_security_hash(self, timestamp):
        """
        Generate the initial security hash from self.content_object
        and a (unix) timestamp.
        """

        initial_security_dict = {
            'timestamp' : str(timestamp),
          }
        return self.generate_security_hash(**initial_security_dict)

    def generate_security_hash(self, timestamp):
        """Generate a (SHA1) security hash from the provided info."""
        info = (timestamp, settings.SECRET_KEY)
        return sha_constructor("".join(info)).hexdigest()
