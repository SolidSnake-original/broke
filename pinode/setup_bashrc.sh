#!/bin/bash

# ShadowBroker bashrc Setup – für User und Root
# by the Architect of the Abyss

set -e

USER_BASHRC="/home/$SUDO_USER/.bashrc"
ROOT_BASHRC="/root/.bashrc"

echo "[+] Configuring User .bashrc for $SUDO_USER"

cat << 'EOF' | sudo tee "$USER_BASHRC" > /dev/null
# Tiefseefarben
BLACK='\[\033[0;30m\]'
DARKGREY='\[\033[1;30m\]'
BLUE='\[\033[0;34m\]'
CYAN='\[\033[0;36m\]'
AQUA='\[\033[1;36m\]'
WHITE='\[\033[1;37m\]'
RESET='\[\033[0m\]'

# Prompt
PS1="${DARKGREY}╭─${AQUA}\u@\h${DARKGREY}:${BLUE}\w\n╰─${CYAN}\$ ${RESET}"

# Aliase
alias ll='ls -la --color=auto'
alias cls='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias g='grep --color=auto'
alias ip='ip a'

# ShadowTools
alias cloak='torify proxychains curl ifconfig.me'
alias whoami-true='id && hostname && who -a'
EOF

echo "[+] User bashrc updated."

echo "[+] Configuring Root .bashrc"

cat << 'EOF' | sudo tee "$ROOT_BASHRC" > /dev/null
# Farben
RED='\[\033[1;31m\]'
DARKRED='\[\033[0;31m\]'
WHITE='\[\033[1;37m\]'
RESET='\[\033[0m\]'

# Prompt – apokalyptisch
PS1="${RED} ☠ ${WHITE}ROOT@$(hostname)${RED} [${DARKRED}\w${RED}] ⚠ ${RESET}"

# Root-only Aliase
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias reboot='echo "🧨 Sicher?" && read -p "Press [y] to continue: " yn && [[ \$yn == y ]] && /sbin/reboot'
alias shutdown='echo "☢ Danger Zone!" && read -p "Shutdown? [y/N]: " yn && [[ \$yn == y ]] && /sbin/shutdown now'

# Tools für rootige Macht
alias monitor='htop || top'
alias netwatch='iftop || nload'
alias audit='ausearch -m avc,user_avc,selinux_err,user_role_change,user_seuser,user_sid,port_bind'

# Banner
echo -e "${RED} ╔═══════════════════════════════════╗"
echo -e "     ║ 🛑  ROOT ZONE ENTERED – have fun  ║"
echo -e "     ╚═══════════════════════════════════╝${RESET}"
EOF

echo "[+] Root bashrc updated."

# Ownership fix
sudo chown "$SUDO_USER:$SUDO_USER" "$USER_BASHRC"

echo ""
echo "⚔️  Die Schatten sind geladen. Teste mit:"
echo "   $ su -   # für Root"
echo "   $ bash   # für User-Neuladen"
