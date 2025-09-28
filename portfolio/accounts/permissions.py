from rest_framework.permissions import BasePermission
from rest_framework import permissions

# class IsOwnerOrAdmin(BasePermission):
#     """
#     Allow portfolio access if:
#     - User is the owner, OR
#     - User is an admin/staff.
#     """
    
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_staff or request.user.is_superuser:
#             return True
#         return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a portfolio to access/modify it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        

        return obj.user == request.user
 