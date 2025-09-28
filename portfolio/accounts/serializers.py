from rest_framework import serializers
from .models import CustomUser



class RegisterSerializer(serializers.ModelSerializer): 
    password = serializers.CharField(write_only=True)
    
    class Meta: 
        model = CustomUser
        fields = ["id", "email", "name", "password"]
        
        
    
    def create(self, validated_data):
        
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data["password"],
            name=validated_data.get("name"),
        )
        
        return user
