from models.database import SessionLocal, User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    # Setting a simple password for easy testing
    u.password_hash = "1234" 
db.commit()
print("Passwords updated to '1234' for all users.")
db.close()
