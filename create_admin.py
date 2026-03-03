from werkzeug.security import generate_password_hash
from models.admin_model import register_admin

print("Creating admin user...")
name = "Admin"
email = "admin@example.com"
password = "admin"

hashed_pw = generate_password_hash(password)

try:
    register_admin(name, email, hashed_pw)
    print(f"✅ Successfully created admin user:\nEmail: {email}\nPassword: {password}")
except Exception as e:
    print(f"❌ Failed to create admin user: {e}")
