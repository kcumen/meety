#!/usr/bin/env python3
import subprocess
import re
import os
import time
import sys

def update_env(new_url):
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        return

    with open(env_path, "r") as f:
        content = f.read()

    if re.search(r"^APP_BASE_URL=.*", content, re.MULTILINE):
        content = re.sub(r"^APP_BASE_URL=.*", f"APP_BASE_URL={new_url}", content, flags=re.MULTILINE)
    else:
        content += f"\nAPP_BASE_URL={new_url}\n"

    with open(env_path, "w") as f:
        f.write(content)
    print(f"✅ Updated .env with APP_BASE_URL={new_url}")

def main():
    print("🚀 Iniciando Localtunnel...")
    # Run localtunnel as a subprocess
    process = subprocess.Popen(
        ["npx", "localtunnel", "--port", "8080"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1 # Line buffered
    )

    url = None
    # Read the first line of output to get the URL
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(f"[LT] {line.strip()}")
        match = re.search(r"(https://[a-zA-Z0-9-]+\.loca\.lt)", line)
        if match:
            url = match.group(1)
            break

    if not url:
        print("❌ No se pudo obtener la URL de Localtunnel.")
        process.kill()
        sys.exit(1)

    # 1. Update .env
    update_env(url)

    # 2. Update Vexa Webhook
    print("🔄 Actualizando Webhook en Vexa...")
    subprocess.run([sys.executable, "scratch/set_webhook.py", url])

    print("\n" + "="*50)
    print(f"✨ Entorno local listo!")
    print(f"🌐 URL Pública: {url}")
    print(f"👉 Asegúrate de que uvicorn esté corriendo (uvicorn app.main:app --reload --port 8080)")
    print("="*50 + "\n")

    # Keep the tunnel alive
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nCerrando Localtunnel...")
        process.terminate()

if __name__ == "__main__":
    main()
