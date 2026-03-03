import os

# 📂 Database Configuration
# Uses environment variables in production, falls back to local 'root/root' for development
db_config = {
    'host': os.getenv('DB_HOST', 'mysql-195da121-adityajadhav3117-3fd9.d.aivencloud.com'),
    'user': os.getenv('DB_USER', 'avnadmin'),
    'password': os.getenv('DB_PASSWORD', 'AVNS_ExdYMuDxC_jtsJiRFkN'),
    'database': os.getenv('DB_NAME', 'defaultdb'),
    'port': int(os.getenv('DB_PORT', 13556))
}

# 📧 Email Configuration (Fetched from environment variables in cloud)
EMAIL_USER = os.getenv('EMAIL_USER', 'adityajadhav3117@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'xmfx rgfi dslk njpg')
