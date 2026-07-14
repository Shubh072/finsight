import unittest

from app import app
from database.db import db
from services.auth_service import register_user, login_user, reset_password
from models.user import User


class AuthWhitespaceTests(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///test_auth.db',
            WTF_CSRF_ENABLED=False,
        )
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_registration_login_and_reset_accept_surrounding_whitespace(self):
        with self.app.app_context():
            reg_response, reg_status = register_user({
                'full_name': '  Alice Example  ',
                'username': '  alice123  ',
                'email': '  alice@example.com  ',
                'phone': ' 12345678 ',
                'password': '  MyPassword1  ',
                'confirm_password': '  MyPassword1  ',
            })

            self.assertEqual(reg_status, 201)
            self.assertTrue(reg_response['success'])

            login_response, login_status = login_user({
                'email': ' alice@example.com ',
                'password': ' MyPassword1 ',
            })

            self.assertEqual(login_status, 200)
            self.assertTrue(login_response['success'])

            user = User.query.filter_by(email='alice@example.com').first()
            self.assertIsNotNone(user)

            reset_response, reset_status = reset_password('dummy-token', {
                'password': '  NewPassword1  ',
                'confirm_password': '  NewPassword1  ',
            })

            self.assertEqual(reset_status, 400)
            self.assertFalse(reset_response['success'])
            self.assertIn('Invalid or expired reset link', reset_response['message'])


if __name__ == '__main__':
    unittest.main()
