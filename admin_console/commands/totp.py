from src.core import auth
u = auth.get_user("benni")
secret = u.get("totp_secret")
import pyotp
print(pyotp.TOTP(secret).provisioning_uri("benni", issuer_name="Mindestentinel"))
