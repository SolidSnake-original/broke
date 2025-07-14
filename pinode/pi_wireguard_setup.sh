#!/bin/bash

# WireGuard-Interface und Pfade
WG_INTERFACE="wg0"
WG_PATH="/etc/wireguard"
WG_CONF="$WG_PATH/${WG_INTERFACE}.conf"

# VPN-Netz
VPN_SERVER_IP="10.6.0.1/24"
VPN_CLIENT_IP="10.6.0.2/32"
VPN_PORT="51820"

# Netzwerkschnittstelle ins Internet (anpassen falls nötig!)
WAN_IFACE="wlan0"

# Sicherheitscheck
if [ "$(id -u)" -ne 0 ]; then
  echo "⚠️  Bitte als root ausführen!"
  exit 1
fi

echo "🧩 Installiere WireGuard..."
apt update && apt install wireguard -y

echo "🔐 Generiere Schlüsselpaare..."
mkdir -p "$WG_PATH"
cd "$WG_PATH"
umask 077
wg genkey | tee server_privatekey | wg pubkey > server_publickey
wg genkey | tee client_privatekey | wg pubkey > client_publickey

SERVER_PRIVATE=$(<server_privatekey)
SERVER_PUBLIC=$(<server_publickey)
CLIENT_PRIVATE=$(<client_privatekey)
CLIENT_PUBLIC=$(<client_publickey)

echo "📝 Erstelle WireGuard-Konfiguration: $WG_CONF"
cat > "$WG_CONF" <<EOF
[Interface]
Address = $VPN_SERVER_IP
ListenPort = $VPN_PORT
PrivateKey = $SERVER_PRIVATE
SaveConfig = true

[Peer]
PublicKey = $CLIENT_PUBLIC
AllowedIPs = $VPN_CLIENT_IP
EOF

chmod 600 "$WG_CONF"

echo "🔁 Aktiviere IP-Forwarding..."
sed -i 's/^#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sysctl -p

echo "🛡️ Setze NAT-Regel für ausgehenden Verkehr über $WAN_IFACE..."
iptables -t nat -A POSTROUTING -o "$WAN_IFACE" -j MASQUERADE
apt install iptables-persistent -y
netfilter-persistent save

echo "🚀 Starte WireGuard..."
systemctl enable wg-quick@$WG_INTERFACE
systemctl start wg-quick@$WG_INTERFACE

echo
echo "🧾 === SERVER-KEYS ==="
echo "Private Key (Server):  $SERVER_PRIVATE"
echo "Public  Key (Server):  $SERVER_PUBLIC"
echo
echo "🧾 === CLIENT-KEYS ==="
echo "Private Key (Client):  $CLIENT_PRIVATE"
echo "Public  Key (Client):  $CLIENT_PUBLIC"
echo

read -p "Drücke [ENTER], um Konsole & Verlauf zu löschen..."

# Konsole und Verlauf löschen
history -c && history -w
clear
echo "🌫️ Alles vergessen. Nichts gesehen. Nichts gesagt."
