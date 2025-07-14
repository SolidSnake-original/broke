#!/bin/bash

# Konfiguration
IFACE="wlan0"
STATIC_IP="10.0.0.211/24"
GATEWAY="10.0.0.1"
DNS1="1.1.1.1"
DNS2="8.8.8.8"
NETFILE="/etc/systemd/network/20-${IFACE}.network"
WPAFILE="/etc/wpa_supplicant/wpa_supplicant-${IFACE}.conf"

# Sicherheitsnetz
if [ "$(id -u)" -ne 0 ]; then
  echo "⚠️  Bitte als root ausführen!"
  exit 1
fi

echo "🧰 Erstelle Network-Datei für $IFACE..."
cat > "$NETFILE" <<EOF
[Match]
Name=$IFACE

[Network]
Address=$STATIC_IP
Gateway=$GATEWAY
DNS=$DNS1
DNS=$DNS2
EOF

echo "🔧 Stelle sicher, dass systemd-networkd aktiv ist..."
systemctl enable systemd-networkd
systemctl restart systemd-networkd

echo "🔧 Aktiviere systemd-resolved..."
systemctl enable systemd-resolved
systemctl restart systemd-resolved
ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf

echo "🧹 Deaktiviere dhcpcd falls aktiv..."
systemctl disable dhcpcd 2>/dev/null
systemctl stop dhcpcd 2>/dev/null

echo "✅ Netzwerk statisch konfiguriert für $IFACE:"
echo "    → IP: $STATIC_IP"
echo "    → Gateway: $GATEWAY"
echo "    → DNS: $DNS1, $DNS2"

# Optional: WPA-Supplicant vorbereiten (nur wenn Datei fehlt)
if [ ! -f "$WPAFILE" ]; then
  echo "📡 WLAN-Konfig $WPAFILE nicht gefunden. Erstelle Dummy-Datei..."
  cat > "$WPAFILE" <<EOW
ctrl_interface=DIR=/run/wpa_supplicant GROUP=netdev
update_config=1
country=AT

network={
    ssid="DEIN_SSID"
    psk="DEIN_PASSWORT"
}
EOW
  chmod 600 "$WPAFILE"
  echo "📝 Bitte WLAN-Zugangsdaten in $WPAFILE eintragen!"
fi

echo "🔌 Aktiviere wpa_supplicant@$IFACE..."
systemctl enable wpa_supplicant@$IFACE
systemctl start wpa_supplicant@$IFACE

echo "🚀 Starte Netzwerksystem neu..."
systemctl restart systemd-networkd

echo "✅ Fertig. Reboot empfohlen für saubere Netzinitialisierung."
