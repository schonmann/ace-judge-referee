#from django.contrib.auth.models import check_password
from django.contrib.auth.models import User
from main.models import Usuario


class StaffBackend:

    # Create an authentication method
    # This is called by the standard Django login procedure
    def authenticate(self, username=None, password=None):

        try:
            # Try to find a user matching your username
	    print username
            user = Usuario.objects.get(username=username)
	    print user
            #  Check the password is the reverse of the username
            if user.check_password(str(password)):
                # Yes? return the Django user object
		print password
                return user
            else:
                # No? return None - triggers default login failed
                return None
        except Usuario.DoesNotExist:
            # No user was found, return None - triggers default login failed
            return None

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
