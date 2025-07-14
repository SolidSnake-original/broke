#!/bin/bash

# ShadowBroker MOTD Setup Script
# Tested on: Debian 12 (Bookworm Lite) / Raspberry Pi OS Lite

set -e

echo "[+] Installing required packages..."
sudo apt update
sudo apt install -y libpam-motd

echo "[+] Creating dynamic MOTD directory..."
sudo mkdir -p /etc/update-motd.d

echo "[+] Writing ShadowBroker MOTD script..."
sudo tee /etc/update-motd.d/01-shadow-broker > /dev/null << 'EOF'
#!/bin/bash

CYAN="\e[36m"
RESET="\e[0m"

echo -e "${CYAN}"
cat << "ART"
      ▄███████████▄
    ▄█▀░░░░░░░░░░▀█▄
   █░░░░░░░░░░░░░░░█    SHADOW BROKER NODE ONLINE
   █░░░░░░░░░░░░░░░█
    ▀█▄▄░░░░░░░░▄▄█▀     ⛧ ENTRY POINT: DEEP SEA NODE π5
        ▀▀████▀▀

ART
echo -e "${RESET}"
echo -e "⏳ Uptime: $(uptime -p)"
echo -e "🧠 Load: $(uptime | awk -F'load average:' '{ print $2 }')"
echo -e "📅 Date: $(date)"
echo -e "🌡️  CPU Temp: $(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 || echo 'Unavailable')"
echo ""
echo -e "🔒 Access Level: ███████▌▌▌"
echo -e "🛰️  Surveillance Status: ENABLED"
echo ""
EOF

echo "[+] Making MOTD script executable..."
sudo chmod +x /etc/update-motd.d/01-shadow-broker

echo "[+] Removing static /etc/motd and linking to dynamic motd..."
sudo rm -f /etc/motd
sudo ln -s /var/run/motd /etc/motd

echo "[+] Verifying PAM configuration for MOTD..."
sudo sed -i '/pam_motd.so/s/^# *//' /etc/pam.d/sshd

echo "[+] ShadowBroker MOTD installed successfully!"
echo ""
echo "🔎 Test it now with:"
echo "   run-parts /etc/update-motd.d/"
echo ""
