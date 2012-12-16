from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

import time
from datetime import datetime, timedelta

import models

def index(request):
    assemblies = (models.Assembly.objects
        .filter(latest_revision__status__isnull=True)
        .filter(latest_revision__date__gt=int(time.mktime((datetime.now() - timedelta(hours=5)).timetuple())))
        .order_by("-latest_revision__date")
        .all())
  
    keywords_raw = models.Config.objects.get(key="keywords").value
    keywords = [keyword.strip() for keyword in keywords_raw.split(u",")]
  
    return render_to_response("index.html", {
        "assemblies": assemblies,
        "keywords_raw": keywords_raw,
        "keywords": keywords
    })

def config(request):
    keywords_raw = models.Config.objects.get(key="keywords").value
    return render_to_response("config.html", {
        "keywords_raw": keywords_raw
    }, context_instance=RequestContext(request))

def save_config(request):
    if request.method == 'POST':
        config = models.Config.objects.get(key="keywords")
        config.value = request.POST.get("config.value", "")
        config.save()
        
        return HttpResponseRedirect(reverse('politiekeagenda.views.config'))
