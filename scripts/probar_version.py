import re, sys, uuid
import httpx
from tricount_extractor.client.keys import generate_public_rsa_key

URL = "https://api.tricount.bunq.com/v1/session-registry-installation"
clave = generate_public_rsa_key()
candidatas = []
for version in ["14.8.2", "14.0.3"]:
    for build in [500004145, 500004150, 500004155, 500004160, 500004165,
                  500004170, 500004180, 500004200, 500005000, 600000000]:
        candidatas.append(f"com.bunq.tricount.android:RELEASE:{version}:{build}:ANDROID:13:C")

for ua in candidatas:
    app = str(uuid.uuid4())
    r = httpx.post(
        URL,
        json={"app_installation_uuid": app, "client_public_key": clave, "device_description": "Android"},
        headers={"User-Agent": ua, "app-id": app,
                 "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
                 "Content-Type": "application/json"},
        timeout=30,
    )
    print(r.status_code, ua)
    if r.status_code < 400:
        ruta = "tricount_extractor/client/client.py"
        codigo = open(ruta).read()
        codigo = re.sub(r'USER_AGENT = ".*?"', f'USER_AGENT = "{ua}"', codigo)
        open(ruta, "w").write(codigo)
        print("FUNCIONA:", ua)
        sys.exit(0)

print("NINGUNA FUNCIONA")
sys.exit(1)
