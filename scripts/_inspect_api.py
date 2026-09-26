from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.deps import user_to_public
from sqlalchemy import select

db = SessionLocal()
users = db.scalars(select(User).order_by(User.id.asc())).all()
print("count", len(users))
for user in users:
    try:
        public = user_to_public(user)
        print(public["id"], public["username"], public["email"], public.get("pii_ok"))
    except Exception as e:
        print("FAIL", user.id, type(e), e)
