from django.test import RequestFactory, TestCase, Client
from .views import profile
from get_model.views import get_model
from django.contrib.auth.models import User

class UsersTest(TestCase):
    def setUp(self):
        self.lv_factory = RequestFactory()
        self.lv_user = User.objects.create_user(username='test_user', password='test_pass', email='test@mail.ru', first_name='101.10.10.101')

    def test_user_profile(self):
        # Создание экземпляра GET запроса.
        lv_request = self.lv_factory.get('/profile')

        # Симуляция входа пользователя через настройку request.user вручную.
        lv_request.user = self.lv_user

        # Тестирование profile() представления.
        lv_response = profile(lv_request)

        # Проверка корректности кода ответа и использованного представления.
        self.assertEqual(lv_response.status_code, 200)

        # Тестирование доступа к get_model() представлению.
        lv_response = get_model(lv_request)
        lv_response.client = Client()
        self.assertRedirects(lv_response, '/login/?next=/profile', status_code=302)

    def test_user_exist(self):
        # Создание экземпляра GET запроса.
        lv_request = self.lv_factory.get('/profile')

        # Получение пользователя из БД.
        lv_user = User.objects.get(username='test_user')

        # Симуляция входа пользователя через настройку request.user вручную.
        lv_request.user = self.lv_user

        # Тестирование profile() представления.
        lv_response = profile(lv_request)

        # Проверка корректности кода ответа.
        self.assertTemplateUsed(lv_response, 'profile.html')