#!/usr/bin/env bash
set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ███████╗██╗██╗     "
echo "  ██╔════╝██║██║     "
echo "  ███████╗██║██║     "
echo "  ╚════██║██║██║     "
echo "  ███████║██║███████╗"
echo "  ╚══════╝╚═╝╚══════╝"
echo -e "${NC}"
echo -e "${PURPLE}Next-Gen macOS Deep Optimizer & AI/Dev Powerhouse Installer${NC}\n"

INSTALL_DIR="$HOME/.local/share/nexus-cli"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

echo "==> Bağımlılıklar ve izole Python ortamı hazırlanıyor..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install rich psutil InquirerPy wcwidth --quiet

echo "==> Kaynak kodlar kopyalanıyor..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR/nexus" "$INSTALL_DIR/"

echo "==> Sembolik bağlantılar oluşturuluyor..."
cat << 'WRAPPER' > "$BIN_DIR/sil"
#!/bin/bash
export PYTHONPATH="$HOME/.local/share/nexus-cli:$PYTHONPATH"
exec "$HOME/.local/share/nexus-cli/venv/bin/python" "$HOME/.local/share/nexus-cli/nexus/main.py" "$@"
WRAPPER
chmod +x "$BIN_DIR/sil"

ln -sf "$BIN_DIR/sil" "$BIN_DIR/nexus"
ln -sf "$BIN_DIR/sil" "$BIN_DIR/mo+"

echo -e "\n${GREEN}✓ 'sil' başarıyla kuruldu!${NC}"
echo -e "Terminalinizde doğrudan ${CYAN}sil${NC} veya ${CYAN}nexus${NC} yazarak başlatabilirsiniz.\n"
