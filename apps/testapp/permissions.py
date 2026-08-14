from rest_framework.permissions import BasePermission, SAFE_METHODS

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTeacherOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        user_role = getattr(request.user, 'role', None)
        return user_role == 'teacher'
