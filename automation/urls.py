from django.urls import path
from . import views

app_name = 'automation'

urlpatterns = [
    path('', views.ai_config, name='ai_config'),
    path('api/generate/', views.api_generate_config, name='api_generate_config'),
    path('api/deploy/', views.api_deploy_config, name='api_deploy_config'),
]