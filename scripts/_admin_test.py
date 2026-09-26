import httpx
import time

base = "http://127.0.0.1:8000"
for _ in range(15):
    try:
        httpx.get(f"{base}/api/health", timeout=1).raise_for_status()
        break
    except Exception:
        time.sleep(0.4)

a = httpx.post(f"{base}/api/auth/login", json={"login": "admin", "password": "admin123"})
print("login", a.status_code)
h = {"Authorization": f"Bearer {a.json()['access_token']}"}

u = httpx.get(f"{base}/api/admin/users", headers=h)
print("users", u.status_code, "count", len(u.json()) if u.status_code == 200 else u.text[:400])
if u.status_code == 200:
    for x in u.json():
        print(" ", x["id"], x["username"], "pii_ok", x.get("pii_ok"))

revs = httpx.get(f"{base}/api/admin/reviews", headers=h)
print("reviews", revs.status_code, "count", len(revs.json()) if revs.status_code == 200 else revs.text[:400])
if revs.status_code == 200 and revs.json():
    rid = revs.json()[0]["id"]
    d = httpx.get(f"{base}/api/admin/reviews/{rid}", headers=h)
    print("detail", d.status_code)
    neg = d.json()
    print(" participants", [(p["id"], p["username"], p.get("score")) for p in neg.get("participants", [])])
    print(" msg labels", [m.get("sender_label") for m in neg.get("messages", [])[:5]])
    parts = neg.get("participants") or []
    if len(parts) > 1:
        body = {"scores": [{"user_id": p["id"], "score": 20 if i == 0 else 70} for i, p in enumerate(parts)]}
    else:
        body = {"score": 55}
    s = httpx.post(f"{base}/api/admin/reviews/{rid}/score", headers=h, json=body)
    print("score", s.status_code, s.text[:250])
