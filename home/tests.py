from django.test import RequestFactory, TestCase
from .views import profile
from django.contrib.auth.models import User

class UsersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test_user', password='test_pass', email='test@mail.ru', first_name='101.10.10.101')

    def test_user_profile(self):
        # Create an instance of a GET request.
        request = self.factory.get('/profile')

        # Simulate a logged-in user by setting request.user manually.
        request.user = self.user

        # Test profile() view
        response = profile(request)

        # Get correct status code
        self.assertEqual(response.status_code, 200)

    def test_admin_exist(self):
        # Create an instance of a GET request.
        request = self.factory.get('/profile')

        user = User.objects.get(username='admin')

        # Simulate a logged-in user by setting request.user manually.
        request.user = self.user

        # Test profile() view
        response = profile(request)

        # Get correct status code
        self.assertEqual(response.status_code, 200)