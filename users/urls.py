from django.urls import path
from .views import LogoutAPIView

urlpatterns = [
    path('logout/', LogoutAPIView.as_view(), name='logout'),
]
