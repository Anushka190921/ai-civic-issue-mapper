from app import get_db
import os

print("Database host:", os.getenv("DB_HOST"))
if input("Create the login_otps table here? Type yes: ").strip().lower() != "yes":
    raise SystemExit("Cancelled.")

db = get_db()
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_otps (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      otp_hash VARCHAR(64) NOT NULL,
      expires_at DATETIME NOT NULL,
      created_at DATETIME NOT NULL,
      attempts INT NOT NULL DEFAULT 0,
      used TINYINT(1) NOT NULL DEFAULT 0,
      INDEX (user_id)
    )
""")
db.commit()
cursor.close()
db.close()
print("Done: login_otps table is ready.")