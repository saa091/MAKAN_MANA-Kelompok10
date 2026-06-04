from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from budget import views as budget_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login/Logout bawaan Django
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Budget app — SATU KALI SAJA dengan namespace
    path('', include(('budget.urls', 'budget'), namespace='budget')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)