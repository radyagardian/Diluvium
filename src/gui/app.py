import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class AdminLogin(BaseModel):
    email: str
    password: str

@app.post("/admin/login")
def login(creds: AdminLogin):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": creds.email,
            "password": creds.password
        })
        return {
            "access_token": res.session.access_token,
            "token_type": "bearer",
            "admin_email": res.user.email
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

@app.get("/admin/system-health")
def get_system_health(authorization: str = Header(...)):
    # Verify the Bearer token with Supabase
    token = authorization.replace("Bearer ", "")
    user = supabase.auth.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {"status": "Healthy", "database": "Connected"}