import subprocess
from datetime import datetime, timezone
import json
import sys
import os
import re

def run_holehe(email):
    """Führt Holehe mit --only-used für die gegebene E-Mail aus und gibt stdout zurück."""
    try:
        result = subprocess.run(
            ["holehe", email, "--only-used"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def parse_holehe_output(output):
    """Extrahiert gefundene Dienste aus dem Holehe-Output, filtert Statuszeile."""
    services = []
    for line in output.strip().splitlines():
        if line.strip().startswith("[+] "):
            service = line.strip()[4:]
            # Filter out summary/status lines
            if "Email used" in service or "not used" in service or "Rate limit" in service:
                continue
            services.append(service)
    return services

def osint_email_holehe(email):
    output = run_holehe(email)
    services = parse_holehe_output(output)
    metadata = {
        "services": services,
        "tool": "holehe",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return metadata

def send_to_gateway(email, metadata, gateway_path="db_faiss_gateway.py", collection="emails"):
    """Überträgt das Ergebnis per CLI an den Gateway."""
    # Übergib metadata als JSON-String
    meta_str = json.dumps(metadata, ensure_ascii=False)
    cmd = [
        sys.executable, gateway_path,
        "add",
        "--collection", collection,
        "--text", email,
        "--metadata", meta_str,
        "--entity_type", "HOLEHE"
    ]
    # Debug: print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.stdout, result.stderr

def log_audit(msg, level="OSINT_EMAIL_HOLEHE"):
    from datetime import datetime
    import os
    now = datetime.now().isoformat(timespec="seconds")
    pid = os.getpid()
    line = f"{now} [{level}] [PID:{pid}] {msg}"
    with open("audit.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def process_email_file(filepath, gateway_path="db_faiss_gateway.py", collection="emails"):
    """
    Liest eine Datei mit E-Mail-Adressen (eine pro Zeile), prüft jede Zeile mit Regex,
    führt für gültige Adressen Holehe aus und fügt sie dem FAISS-Gateway hinzu.
    Ungültige Zeilen werden ins Audit-Log geschrieben.
    """
    email_regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            email = line.strip()
            if not email:
                continue
            if not email_regex.match(email):
                log_audit(f"Ungültige E-Mail in Datei: '{email}'", level="INVALID_EMAIL")
                continue
            metadata = osint_email_holehe(email)
            out, err = send_to_gateway(email, metadata, gateway_path=gateway_path, collection=collection)
            log_audit(f"Holehe/FAISS verarbeitet: {email} | Gateway stdout: {out.strip()} | stderr: {err.strip() if err else 'None'}", level="BULK_HOLEHE")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python osint_email_holehe.py <email> [--no-gateway]")
        exit(1)
    email = sys.argv[1]
    metadata = osint_email_holehe(email)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # Wenn "--no-gateway" angegeben ist, nur Ausgabe, kein Insert
    if "--no-gateway" not in sys.argv:
        out, err = send_to_gateway(email, metadata)
        print("\n[Gateway stdout]")
        print(out)
        if err:
            print("[Gateway stderr]")
            print(err)
