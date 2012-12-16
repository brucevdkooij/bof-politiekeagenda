from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'politiekeagenda.views.index', name='index'),
    url(r'^config$', 'politiekeagenda.views.config', name='config'),
    url(r'^save_config$', 'politiekeagenda.views.save_config', name='save_config'),
)
