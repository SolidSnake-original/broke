#!/bin/bash

# ==================== KONFIGURATION ====================
TARGET_IP="10.0.0.211"
WG_PORT=51820
SOCKS_PORT=9050
WG_IFACE="wg0"
WLAN_IFACE="wlan0"
TOR_HS_DIR="/var/lib/tor/ssh_hidden"
EMAIL="p.holubarz@gmail.com"
LOGDIR="/home/elderberry/piscriptshare/logs"
LOGFILE="$LOGDIR/pinode.log"
SCRIPTNAME="netzwerk_watchdog.sh"

# ==================== FUNKTIONEN =======================
mkdir -p "$LOGDIR"

log_msg() {
  local LEVEL="$1"
  shift
  local MSG="$*"
  local TS="$(date '+%Y-%m-%d %H:%M:%S')"
  local PID="$$"
  echo "$TS|$PID|$SCRIPTNAME|$LEVEL|$MSG" >> "$LOGFILE"
}

log() {
  log_msg info "$@"
}

log_warn() {
  log_msg warn "$@"
}

log_error() {
  log_msg error "$@"
}

fail() {
  log_error "$1"
  send_mail "❌ Fehler auf $(hostname)" "$1"
  exit 1
}

send_mail() {
  TO="$EMAIL"
  SUBJECT="$1"
  BODY="$2"

  echo -e "To: $TO\nSubject: $SUBJECT\n\n$BODY" | msmtp -t
}

# ==================== NETZWERK CHECK ====================
log "Überprüfe IP $TARGET_IP auf $WLAN_IFACE..."
if ip addr show "$WLAN_IFACE" | grep -q "$TARGET_IP"; then
  log "✅ IP vorhanden."
else
  log_warn "⚠️ IP fehlt. Versuche Reparatur..."

  log "Aktiviere wpa_supplicant@$WLAN_IFACE..."
  systemctl enable wpa_supplicant@$WLAN_IFACE
  systemctl restart wpa_supplicant@$WLAN_IFACE

  log "Starte DHCP..."
  systemctl enable dhcpcd
  systemctl restart dhcpcd

  sleep 5
  ip addr show "$WLAN_IFACE" | grep "$TARGET_IP" || fail "Netzwerk konnte nicht repariert werden."
  log "✅ Verbindung wiederhergestellt."
fi

# ==================== DIENSTE ===========================

# WireGuard
log "Prüfe WireGuard..."
if ! wg show "$WG_IFACE" &>/dev/null; then
  log "Starte WireGuard..."
  systemctl restart wg-quick@"$WG_IFACE"
  sleep 3
fi

# Tor
log "Prüfe Tor..."
systemctl is-active --quiet tor || systemctl restart tor

# Hidden Service
if [ -f "$TOR_HS_DIR/hostname" ]; then
  ONION=$(cat "$TOR_HS_DIR/hostname")
  log "Onion erreichbar unter: $ONION"
else
  log_warn "⚠️ Kein Onion-Link gefunden."
fi

# ==================== FIREWALL SETUP ====================

log "Prüfe UFW-Installation..."
if ! command -v ufw &>/dev/null; then
  log "Installiere UFW..."
  apt update && apt install ufw -y || fail "UFW-Installation gescheitert!"
fi

log "Setze restriktive Firewall-Regeln..."

# Reset & Default-Policies
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# WireGuard (UDP)
ufw allow "$WG_PORT"/udp comment "WireGuard VPN"

# Tor SOCKS (lokaler Zugriff)
ufw allow in on lo to any port "$SOCKS_PORT" proto tcp comment "Tor SOCKS (localhost only)"

# SSH (nur intern oder wg0 – auf Wunsch restriktiver)
ufw allow in on "$WLAN_IFACE" to any port 22 proto tcp comment "SSH WLAN intern"
ufw allow in on "$WG_IFACE" to any port 22 proto tcp comment "SSH via VPN"

# Aktivieren
ufw --force enable
ufw reload

# ==================== ABSCHLUSS ========================

STATUS=$(ip -br addr show "$WLAN_IFACE" | grep "$TARGET_IP" && systemctl is-active wg-quick@"$WG_IFACE" && systemctl is-active tor)

send_mail "✅ Netzwerk OK auf $(hostname)" "IP: $TARGET_IP\nWireGuard, Tor, SOCKS erfolgreich aktiv.\nOnion: $ONION"

log "🛡️  Netzwerk-Wächter vollständig abgeschlossen."
exit 0
