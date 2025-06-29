import sys
import subprocess
import importlib.util
import pkg_resources

# Mindestpakete für ChromaDB + Standard-Tools (anpassbar)
REQUIREMENTS = [
    "chromadb",
    "sentence-transformers",
    "rich"
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

def test_chromadb():
    print("[+] Starte ChromaDB-Check...")
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.Client(Settings(
            persist_directory="./chroma_data"
        ))
        col = client.create_collection("test_collection")
        col.add(
            documents=["Dies ist ein Testdokument für den Shadow Broker."],
            metadatas=[{"source": "Installer"}],
            ids=["test1"]
        )
        results = col.query(query_texts=["Shadow Broker"], n_results=1)
        print("[+] ChromaDB funktioniert! Query-Ergebnis:")
        print(results)
        print("[SUCCESS] ChromaDB ist einsatzbereit.")
    except Exception as e:
        print("[ERROR] ChromaDB-Test fehlgeschlagen:", e)
        sys.exit(1)

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
    test_chromadb()
    check_sqlite()
    print("\n[+] Setup abgeschlossen. Du kannst jetzt Module andocken.\n")

if __name__ == "__main__":
    main()
