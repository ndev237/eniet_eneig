"""
URL configuration for ENIET/ENIEG project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.views.generic import RedirectView   # ← Nouveau

# URLs SANS préfixe de langue
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('tinymce/', include('tinymce.urls')),

    path('', RedirectView.as_view(url='/fr/', permanent=False), name='root_redirect'),
]

# URLs AVEC préfixe de langue : /fr/... et /en/...
urlpatterns += i18n_patterns(
    path('', include('apps.core.urls')),
    path('ecole/', include('apps.pages.urls')),
    path('formations/', include('apps.ecoles.urls')),
    path('actualites/', include('apps.blog.urls')),
    path('contact/', include('apps.contacts.urls')),

    path('admission/', RedirectView.as_view(pattern_name='ecoles:admission', permanent=True), name='admission_legacy'),
    prefix_default_language=True,

)


# Servir les fichiers média uniquement en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)