# config.py
import os

# إعدادات التطبيق
SECRET_KEY = os.environ.get("SECRET_KEY", "mim_marketing_secret_key_2026")
DEBUG = False  # مهم: False في الإنتاج

# إعدادات Telegram
API_ID = 39289901
API_HASH = "a5dcef068387dd95705046f910d6cd48"

# قاعدة البيانات - استخدام مسار مؤقت لـ Railway
DATABASE = os.path.join("/tmp", "mim_marketing.db")

# مجلد الجلسات - مسار مؤقت
SESSION_FILE_DIR = "/tmp/flask_session"

# المشرف
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_ID = 5064913080
