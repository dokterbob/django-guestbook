from django import http
from django.conf import settings
from utils import next_redirect, confirmation_view
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
from django.contrib import guestbook
from django.contrib.guestbook import signals

class EntryPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a entry post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """
    def __init__(self, why):
        super(EntryPostBadRequest, self).__init__()
        if settings.DEBUG:
            self.content = render_to_string("guestbook/400-debug.html", {"why": why})

def post_entry(request, next=None):
    """
    Post a entry.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``guestbook/preview.html``, will be rendered.
    """

    # Require POST
    if request.method != 'POST':
        return http.HttpResponseNotAllowed(["POST"])

    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name()
        if not data.get('email', ''):
            data["email"] = request.user.email

    # Do we want to preview the entry?
    preview = data.get("submit", "").lower() == "preview" or \
              data.get("preview", None) is not None

    # Construct the entry form
    form = guestbook.get_form()(target, data=data)

    # Check security information
    if form.security_errors():
        return EntryPostBadRequest(
            "The entry form failed security verification: %s" % \
                escape(str(form.security_errors())))

    # If there are errors or if we requested a preview show the entry
    if form.errors or preview:
        template_list = [
            "guestbook/%s_%s_preview.html" % tuple(str(model._meta).split(".")),
            "guestbook/%s_preview.html" % model._meta.app_label,
            "guestbook/preview.html",
        ]
        return render_to_response(
            template_list, {
                "entry" : form.data.get("entry", ""),
                "form" : form,
            }, 
            RequestContext(request, {})
        )

    # Otherwise create the entry
    entry = form.get_entry_object()
    entry.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        entry.user = request.user

    # Signal that the entry is about to be saved
    responses = signals.entry_will_be_posted.send(
        sender  = entry.__class__,
        entry = entry,
        request = request
    )

    for (receiver, response) in responses:
        if response == False:
            return EntryPostBadRequest(
                "entry_will_be_posted receiver %r killed the entry" % receiver.__name__)

    # Save the entry and signal that it was saved
    entry.save()
    signals.entry_was_posted.send(
        sender  = entry.__class__,
        entry = entry,
        request = request
    )

    return next_redirect(data, next, entry_done, c=entry._get_pk_val())

entry_done = confirmation_view(
    template = "guestbook/posted.html",
    doc = """Display a "entry was posted" success page."""
)

