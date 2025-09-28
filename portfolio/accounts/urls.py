from django.urls import path
from .views import RegisterView, AccountListView



urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("list/", AccountListView.as_view(), name="list_accouns")
    
    

]


