from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
 
urlpatterns = [
    path('cases/', views.my_cases, name='my_cases'),
    path('cases/<int:pk>/', views.case_detail, name='case_detail'),
    path('cases/<int:pk>/add-update/', views.add_update, name='add_update'),
    path('cases/<int:pk>/evidence/', views.upload_evidence, name='upload_evidence'),
    path('cases/<int:pk>/close/', views.close_case, name='close_case'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:pk>/', views.messages_view, name='messages_case'),
]
 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)