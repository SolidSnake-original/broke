import sys
import subprocess
import importlib.util
import pkg_resources

# Mindestpakete für ChromaDB + Standard-Tools (anpassbar)
REQUIREMENTS = [
    "sentence-transformers",
    "rich",
    "faiss-cpu",
    "numpy",
    "prompt_toolkit",
    "setuptools"
]

def pip_install(pkg):
    print(f"[+] Installiere {pkg} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def check_and_install(pkg):
    try:
        dist = pkg_resources.get_distribution(pkg)
        print(f"[+] {pkg} ist bereits installiert ({dist.version})")
    except pkg_resources.DistributionNotFound:
        pip_install(pkg)

def install_requirements():
    print("[+] Prüfe und installiere erforderliche Pakete...")
    for pkg in REQUIREMENTS:
        check_and_install(pkg)

def check_sqlite():
    try:
        import sqlite3
        print("[+] sqlite3-Modul ist verfügbar (builtin).")
    except ImportError:
        print("[ERROR] sqlite3-Modul fehlt. Bitte installiere ein vollwertiges Python mit sqlite3-Unterstützung.")
        sys.exit(1)

def main():
    print("\n[Shadow Broker Installer – ChromaDB Bootstrap]\n")
    install_requirements()
    check_sqlite()
    print("\n[+] Setup abgeschlossen. Du kannst jetzt Module andocken.\n")

if __name__ == "__main__":
    main()
