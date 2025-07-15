#!/bin/bash

WG_IFACE="wg0"
WG_CONF="/etc/wireguard/wg0.conf"
TOR_SRC_IP="10.6.0.1"
TABLE_ID="100"
TABLE_NAME="torroute"

# --- Logging Funktion ---
LOGDIR="/home/elderberry/piscriptshare/logs"
LOGFILE="$LOGDIR/pinode.log"
SCRIPTNAME="setup_tor_route.sh"
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

# 1. WireGuard aktivieren oder reinitialisieren
if ! ip link show "$WG_IFACE" | grep -q "state UP"; then
  if ip link show "$WG_IFACE" &>/dev/null; then
    log_warn "$WG_IFACE existiert aber ist nicht aktiv – entferne Zombie..."
    ip link delete "$WG_IFACE"
  fi

  log "Starte $WG_IFACE neu über wg-quick..."
  if [ -f "$WG_CONF" ]; then
    wg-quick up "$WG_IFACE" || { log_error "[❌] WireGuard konnte nicht gestartet werden."; exit 1; }
    log "$WG_IFACE erfolgreich gestartet."
  else
    log_error "[❌] Keine Konfigdatei gefunden unter $WG_CONF. Abbruch."
    exit 1
  fi
else
  log "$WG_IFACE ist bereits aktiv."
fi

# 1b. Tor-Dienst prüfen und ggf. starten
if systemctl is-active --quiet tor; then
  log "Tor-Dienst läuft bereits."
else
  log_warn "Starte Tor-Dienst..."
  systemctl restart tor
  sleep 2
  if systemctl is-active --quiet tor; then
    log "Tor-Dienst erfolgreich gestartet."
  else
    log_error "[❌] Tor-Dienst konnte nicht gestartet werden. Abbruch."
    exit 1
  fi
fi

# 2. Routingtabelle eintragen
grep -q "$TABLE_NAME" /etc/iproute2/rt_tables || {
  echo "$TABLE_ID $TABLE_NAME" >> /etc/iproute2/rt_tables
  log "Routingtabelle $TABLE_NAME (ID $TABLE_ID) hinzugefügt."
}

# 3. Route setzen
if ! ip route show table "$TABLE_NAME" | grep -q default; then
  log "Setze default-Route in Tabelle $TABLE_NAME über $WG_IFACE..."
  ip route add default dev "$WG_IFACE" table "$TABLE_NAME"
else
  log "Default-Route in $TABLE_NAME existiert bereits."
fi

# 4. Regel für TOR-IP setzen
if ! ip rule | grep -q "from $TOR_SRC_IP.*$TABLE_NAME"; then
  log "Setze IP-Regel: from $TOR_SRC_IP → $TABLE_NAME"
  ip rule add from "$TOR_SRC_IP" table "$TABLE_NAME"
else
  log "IP-Regel für $TOR_SRC_IP bereits vorhanden."
fi

log "✅ Tor-Routing über WireGuard ist aktiv."
