from app import db, User

# Define the admin user's email
admin_email = "admin.admin@omnipol.cz"

# Query the user
user = User.query.filter_by(username=admin_email).first()

if user:
    user.is_admin = True
    db.session.commit()
    print(f"User {admin_email} is now an admin.")
else:
    print(f"User {admin_email} does not exist.")
