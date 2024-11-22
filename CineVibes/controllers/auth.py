import sqlite3
import random
import string
from werkzeug.security import generate_password_hash
from utils.email import send_verification_email

class AuthController:
    def __init__(self, db_path):
        self.db_path = db_path

    def register(self, nickname, email, password):
        # Generar un código de verificación
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Guardar el usuario con el código de verificación
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (nickname, email, password, verification_code, is_verified)
                VALUES (?, ?, ?, ?, ?)
            ''', (nickname, email, generate_password_hash(password), verification_code, False))
            user_id = cursor.lastrowid

        # Enviar el correo de verificación
        send_verification_email(email, verification_code)

        return user_id

    def verify_code(self, email, code):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Establecer row_factory aquí
            cursor = conn.cursor()
            user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if user and user['verification_code'] == code:
                # Marcar al usuario como verificado
                cursor.execute('UPDATE users SET is_verified = TRUE WHERE id = ?', (user['id'],))
                conn.commit()
                return True
        return False

    def get_user_profile(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Asegúrate de que esto esté aquí también
            cursor = conn.cursor()
            user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if user:
                return {
                    'id': user['id'],
                    'nickname': user['nickname'],
                    'email': user['email'],
                    'profile_pic': user['profile_pic'],
                    'is_verified': user['is_verified']
                }
        return None

    def update_profile_pic(self, user_id, profile_pic_path):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE users SET profile_pic = ? WHERE id = ?',
                (profile_pic_path, user_id)
            )
            conn.commit()

    def update_user_profile(self, user_id, nickname, email, password):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Actualizar nickname y email
            cursor.execute('''
                UPDATE users
                SET nickname = ?, email = ?
                WHERE id = ?
            ''', (nickname, email, user_id))

            # Si se proporciona una nueva contraseña, actualizarla
            if password:
                hashed_password = generate_password_hash(password)
                cursor.execute('''
                    UPDATE users
                    SET password = ?
                    WHERE id = ?
                ''', (hashed_password, user_id))

            conn.commit()

            # Verificar si se realizaron cambios if cursor.rowcount > 0:
            return True
        return False
