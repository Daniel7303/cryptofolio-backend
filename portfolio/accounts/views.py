from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import CustomUser
from .serializers import RegisterSerializer




class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    
    
class AccountListView(generics.ListCreateAPIView):
    serializer_class = RegisterSerializer
    
    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=False)
        
