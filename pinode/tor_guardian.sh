#!/bin/bash

# Konfiguration
WG_IFACE="wg0"
TOR_SRC_IP="10.6.0.1"
TABLE_ID="100"
TABLE_NAME="torroute"
LOGFILE="/var/log/tor_guardian.log"
EMAIL="p.holubarz@gmail.com"

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

# --- Logging Funktion ---
LOGDIR="/home/elderberry/piscriptshare/logs"
LOGFILE="$LOGDIR/pinode.log"
SCRIPTNAME="tor_guardian.sh"
mkdir -p "$LOGDIR"

log_msg() {
  local LEVEL="$1"
  shift
  local MSG="$*"
  local TS="$(date '+%Y-%m-%d %H:%M:%S')"
  local PID="$$"
  echo "$TS|$PID|$SCRIPTNAME|$LEVEL|$MSG" >> "$LOGFILE"
}

# Alte log()-Funktion ersetzen:
log() {
  log_msg info "$@"
}

log_warn() {
  log_msg warn "$@"
}

log_error() {
  log_msg error "$@"
}

notify() {
  echo -e "To: $EMAIL\nSubject: [Tor Guardian] $1\n\n$2" | msmtp -t
}

# Status-Tracker
STATUS_FILE="/tmp/.tor_guardian_last_status"
LAST_STATUS="UNKNOWN"
[ -f "$STATUS_FILE" ] && LAST_STATUS=$(cat "$STATUS_FILE")

# Prüfen ob wg0 up (akzeptiere auch state UNKNOWN)
WG_STATE=$(ip link show "$WG_IFACE" 2>/dev/null | grep -o 'state [A-Z]*' | awk '{print $2}')
if [ -z "$WG_STATE" ]; then
  log_warn "⚠️ $WG_IFACE existiert nicht – versuche zu starten..."
  wg-quick up "$WG_IFACE"
  sleep 2
  WG_STATE=$(ip link show "$WG_IFACE" 2>/dev/null | grep -o 'state [A-Z]*' | awk '{print $2}')
fi
if [ "$WG_STATE" != "UP" ] && [ "$WG_STATE" != "UNKNOWN" ]; then
  [ "$LAST_STATUS" != "DOWN" ] && notify "WireGuard DOWN" "Interface $WG_IFACE ist nicht aktiv (state: $WG_STATE)."
  log_error "❌ $WG_IFACE down (state: $WG_STATE) → Tor wird gestoppt."
  systemctl stop tor
  echo "DOWN" > "$STATUS_FILE"
  exit 0
fi

# Prüfen ob Route vorhanden
if ! ip route show table "$TABLE_NAME" | grep -q default; then
  [ "$LAST_STATUS" != "DOWN" ] && notify "Routing fehlt" "Keine default route in $TABLE_NAME über $WG_IFACE."
  log_error "❌ Route fehlt → Tor wird gestoppt."
  systemctl stop tor
  echo "DOWN" > "$STATUS_FILE"
  exit 0
fi

# Prüfen ob Rule da
if ! ip rule | grep -q "from $TOR_SRC_IP.*$TABLE_NAME"; then
  [ "$LAST_STATUS" != "DOWN" ] && notify "IP Rule fehlt" "Keine IP-Regel für $TOR_SRC_IP in $TABLE_NAME."
  log_error "❌ IP-Regel fehlt → Tor wird gestoppt."
  systemctl stop tor
  echo "DOWN" > "$STATUS_FILE"
  exit 0
fi

# Prüfen ob Routing wirklich über wg0 geht
ACTUAL_IFACE=$(ip route get 1.1.1.1 from "$TOR_SRC_IP" | grep -o "dev [a-z0-9]*" | awk '{print $2}')
if [ "$ACTUAL_IFACE" != "$WG_IFACE" ]; then
  [ "$LAST_STATUS" != "DOWN" ] && notify "Tor Routing Leak!" "Tor würde über $ACTUAL_IFACE statt $WG_IFACE gehen."
  log_error "❌ Routing Leak → Tor wird gestoppt."
  systemctl stop tor
  echo "DOWN" > "$STATUS_FILE"
  exit 0
fi

# Alles okay – prüfe ob Tor läuft
if systemctl is-active --quiet tor; then
  log "✅ Tor läuft bereits – alles in Ordnung."
else
  log_warn "⚠️ Tor ist NICHT aktiv, starte neu..."
  systemctl start tor
  notify "Tor neu gestartet" "Tor wurde reaktiviert, da die Route wieder korrekt ist."
fi

echo "UP" > "$STATUS_FILE"
