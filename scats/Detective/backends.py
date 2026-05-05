from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class PersonnelOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print("LOGIN ATTEMPT:", username)

        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
            print("USER FOUND:", user.username)
        except User.DoesNotExist:
            print("USER NOT FOUND")
            return None

        if user.check_password(password):
            print("PASSWORD CORRECT")
            return user

        print("WRONG PASSWORD")
        return None