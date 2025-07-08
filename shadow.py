import subprocess
import platform
import os
import time
import sys
import requests

WIREGUARD_PROFILE = "C:\\Pfad\\zu\\BrokerTunnel.conf"  # Windows
TOR_PATH = "C:\\Users\\Admin\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"
PROXYCHAINS_PATH = "/usr/bin/proxychains4"  # Linux
LINUX_WG_CONF = "/etc/wireguard/broker.conf"

def start_wireguard():
    if platform.system() == "Windows":
        subprocess.run(["C:\\Program Files\\WireGuard\\wireguard.exe", "/installtunnelservice", WIREGUARD_PROFILE])
    elif platform.system() == "Linux":
        subprocess.run(["wg-quick", "up", LINUX_WG_CONF])

def stop_wireguard():
    if platform.system() == "Windows":
        subprocess.run(["C:\\Program Files\\WireGuard\\wireguard.exe", "/uninstalltunnelservice", WIREGUARD_PROFILE])
    elif platform.system() == "Linux":
        subprocess.run(["wg-quick", "down", LINUX_WG_CONF])

def start_tor():
    if platform.system() == "Windows":
        return subprocess.Popen([TOR_PATH])
    elif platform.system() == "Linux":
        return subprocess.Popen(["tor"])
    return None

def set_proxy_env():
    # Tor SOCKS5
    os.environ["HTTP_PROXY"] = "socks5h://127.0.0.1:9050"
    os.environ["HTTPS_PROXY"] = "socks5h://127.0.0.1:9050"
    os.environ["ALL_PROXY"] = "socks5h://127.0.0.1:9050"

def ip_check():
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=10)
        print(f"[+] Öffentliche IP laut ipify: {r.json()['ip']}")
    except Exception as e:
        print(f"[!] IP Check fehlgeschlagen: {e}")

def dns_leak_check():
    try:
        r = requests.get("https://dnsleaktest.com/api/v1/scan", timeout=15)
        print("[+] DNS Leak Test: ", r.json())
    except Exception as e:
        print(f"[!] DNS Leak Test fehlgeschlagen: {e}")

def main():
    print("[*] Starte WireGuard...")
    start_wireguard()
    time.sleep(5)
    print("[*] Starte Tor...")
    tor_proc = start_tor()
    time.sleep(15)
    print("[*] Setze Proxy-Umgebung...")
    set_proxy_env()
    print("[*] Prüfe externe IP...")
    ip_check()
    print("[*] Prüfe DNS Leaks...")
    dns_leak_check()
    print("[*] Deine Schattenroute ist aktiv.")
    print("[*] Zum Beenden Ctrl+C drücken.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[*] Fahre alles herunter...")
        stop_wireguard()
        if tor_proc:
            tor_proc.terminate()
        print("[*] Schatten verblassen.")

if __name__ == "__main__":
    main()
