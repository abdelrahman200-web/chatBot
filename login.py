from flask_login import UserMixin, LoginManager
import sqlite3

# 🔹 إعداد Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"  # توجيه المستخدم إلى صفحة تسجيل الدخول عند عدم المصادقة

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id  # يجب أن يكون `id` رقمًا وليس `username`
        self.username = username
        self.password = password

# 🔹 تحميل المستخدم من قاعدة البيانات
@login_manager.user_loader
def load_user(user_id):
    connection = sqlite3.connect("whatsapp_bot")
    cursor = connection.cursor()
    cursor.execute("SELECT username, password_hash FROM admin WHERE username = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    
    if user:
        return User(user_id=user[0], username=user[0], password=user[1])  # ✅ إرجاع الكائن الصحيح
    return None

# 🔹 التحقق من بيانات تسجيل الدخول
def check_login(username, password):
    connection = sqlite3.connect("whatsapp_bot")
    cursor = connection.cursor()
    cursor.execute("SELECT username, password_hash FROM admin WHERE username = ?", (username,))
    user = cursor.fetchone()
    connection.close()
    
    if user and user[1] == password:
        return User(user_id=user[0], username=user[0], password=user[1])  # ✅ إرجاع كائن المستخدم
    return None
