import os

# 📂 Database Configuration
# Uses environment variables in production, falls back to local 'root/root' for development
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'donation'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# 📧 Email Configuration (Fetched from environment variables in cloud)
EMAIL_USER = os.getenv('EMAIL_USER', 'adityajadhav3117@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'xmfx rgfi dslk njpg')
