#!/bin/bash

# Konfiguration
WG_PORT=51820
SSH_PORT=22
WAN_IFACE="wlan0"

# Sicherheitsprüfung
if [ "$(id -u)" -ne 0 ]; then
  echo "⚠️  Bitte als root ausführen!"
  exit 1
fi

echo "🔥 Installiere UFW falls nicht vorhanden..."
apt update && apt install ufw -y

echo "🧱 Setze Default-Policies..."
ufw default deny incoming
ufw default allow outgoing

echo "🔓 Erlaube eingehende Verbindungen:"
ufw allow $SSH_PORT/tcp comment "SSH-Zugang"
ufw allow $WG_PORT/udp comment "WireGuard"

echo "📡 Erlaube IP-Weiterleitung in UFW..."
UFW_SYSCTL="/etc/ufw/sysctl.conf"
sed -i 's/^#\(net.ipv4.ip_forward=1\)/\1/' "$UFW_SYSCTL"
sed -i 's/^#\(net.ipv6.conf.all.forwarding=1\)/\1/' "$UFW_SYSCTL"

echo "🪄 Füge NAT-Regel hinzu für WireGuard..."
UFW_BEFORE_RULES="/etc/ufw/before.rules"

# Backup
cp "$UFW_BEFORE_RULES" "$UFW_BEFORE_RULES.bak"

# Falls noch nicht vorhanden, NAT-Sektion hinzufügen
if ! grep -q "WireGuard NAT" "$UFW_BEFORE_RULES"; then
  sed -i "1i\
# WireGuard NAT\n*nat\n:POSTROUTING ACCEPT [0:0]\n-A POSTROUTING -s 10.6.0.0/24 -o $WAN_IFACE -j MASQUERADE\nCOMMIT\n" "$UFW_BEFORE_RULES"
fi

echo "✅ Aktiviere UFW..."
ufw --force enable

echo "🔍 UFW Status:"
ufw status verbose

echo "🧼 Alles bereit – Ports offen:"
echo "    → SSH auf $SSH_PORT"
echo "    → WireGuard auf $WG_PORT/udp"
echo "📦 Forwarding & NAT sind konfiguriert über $WAN_IFACE"
