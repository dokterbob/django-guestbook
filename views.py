from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader

from django.core.paginator import ObjectPaginator, InvalidPage

from django import forms

from amfibi.guestbook.models import *
from amfibi.site.models import *

from accesscontrol.models import is_blocked

def last_page(request):
    paginator = ObjectPaginator(Entry.objects.filter(activated=True), 4, orphans=2)
    topage = paginator.pages
    return HttpResponseRedirect('%d/' % topage)

def guestbook_list(request, page, errors=None):
    m = Menu.objects.filter(activated=True)
    p = Menu.objects.get(slug='gastenboek').mainpage
    paginator = ObjectPaginator(Entry.objects.filter(activated=True), 4, orphans=2)

    page = int(page)-1
    e = paginator.get_page(page)

    manipulator = Entry.AddManipulator()
    f = forms.FormWrapper(manipulator, {}, {})

    if paginator.has_next_page(page):
        next_page = page+2
    else:
        next_page = None

    if paginator.has_previous_page(page):
        previous_page = page
    else:
        previous_page = None

    env = { 'menu':m,
            'page':p,
            'current_page' : page+1,
            'next_page': next_page,
            'previous_page': previous_page,
            'entries': e,
            'form': f
          }

    return render_to_response('guestbook_list.html', env)

def add_entry(request):
    new_data = request.POST.copy()
    manipulator = Entry.AddManipulator()
    e = manipulator.get_validation_errors(new_data)
    manipulator.do_html2python(new_data)
    ip = request.META.get('REMOTE_ADDR')
    #host = gethostbyaddr(ip)[0]
    new_data.update({'ip':ip, 'activated':True})
    
    #manipulator.ip = request.META.get('REMOTE_ADDR')
    #lasthour = datetime.datetime.now() - datetime.timedelta(hours=1)
    #hourcount = Entry.objects.filter(ip__exact=ip, date_add__gte=lasthour).count()

    o = None
    if is_blocked(ip):
        o = "Vanaf jouw IP-adres (%s) is het op dit moment niet toegestaan om berichten toe te voegen. Probeer het later nog eens." % ip
    elif not e:
        print "Entry added"
        manipulator.save(new_data)

    print o, e

    m = Menu.objects.filter(activated=True)
    p = Menu.objects.get(slug='fotos').mainpage
    
    env = { 'menu':m,
            'page':p,
            'errors':e,
            'othererror':o
          }

    return render_to_response('guestbook_add_result.html', env)

