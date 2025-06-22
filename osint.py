import subprocess
import sys
import importlib.util
import shutil

def pip_install(pkg):
    print(f"[+] Installiere {pkg} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def check_and_install(tool, pkg=None):
    # Prüft, ob ein CLI-Tool vorhanden ist, sonst pip-install
    if pkg is None:
        pkg = tool
    if shutil.which(tool) is None:
        print(f"[!] {tool} nicht gefunden. Installiere...")
        pip_install(pkg)

def sherlock_cli():
    username = input("Gib den Username ein: ").strip()
    print(f"[+] Suche Social Media Profile für: {username}")
    try:
        cmd = f'sherlock "{username}" --print-found --nsfw'
        subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        print(f"[!] Fehler beim Sherlock-Start: {e}")

def holehe_cli():
    email = input("Gib die Ziel-E-Mail-Adresse ein: ").strip()
    print(f"[+] Prüfe Registrierungen für: {email}")
    try:
        cmd = f'holehe "{email}" -C'
        subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        print(f"[!] Fehler beim holehe-Start: {e}")

def theharvester_cli():
    domain = input("Gib die Ziel-Domain ein (z.B. example.com): ").strip()
    limit = input("Wieviele Ergebnisse? (default: 100): ").strip()
    if not limit.isdigit():
        limit = "100"
    print(f"[+] Suche Informationen für Domain: {domain}")
    try:
        cmd = f'theHarvester -d "{domain}" -b all -l {limit}'
        subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        print(f"[!] Fehler beim theHarvester-Start: {e}")

def main_menu():
    while True:
        print("\n" + "="*35)
        print("OSINT BROKER – Hauptmenü")
        print("="*35)
        print("[1] Sherlock – Usernamen suchen")
        print("[2] holehe – Email auf Plattformen prüfen")
        print("[3] theHarvester – Domains ausspionieren")
        print("[q] Beenden")
        choice = input("Auswahl: ").strip().lower()
        if choice == "1":
            sherlock_cli()
        elif choice == "2":
            holehe_cli()
        elif choice == "3":
            theharvester_cli()
        elif choice == "q":
            print("Bye, Broker!")
            break
        else:
            print("Ungültige Auswahl.")

if __name__ == "__main__":
    check_and_install("sherlock")
    check_and_install("holehe")
    check_and_install("theHarvester")
    main_menu()
