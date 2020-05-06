from django.test import RequestFactory, TestCase
from .views import profile
from django.contrib.auth.models import User

class UsersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test_user', password='test_pass', email='test@mail.ru', first_name='101.10.10.101')

    def test_user_profile(self):
        # Создание экземпляра GET запроса.
        request = self.factory.get('/profile')

        # Симуляция входа пользователя через настройку request.user вручную.
        request.user = self.user

        # Тестирование profile() представления.
        response = profile(request)

        # Проверка корректности кода ответа.
        self.assertEqual(response.status_code, 200)

    def test_user_exist(self):
        # Создание экземпляра GET запроса.
        request = self.factory.get('/profile')

        user = User.objects.get(username='test_user')

        # Симуляция входа пользователя через настройку request.user вручную.
        request.user = self.user

        # Тестирование profile() представления.
        response = profile(request)

        # Проверка корректности кода ответа.
        self.assertEqual(response.status_code, 200)