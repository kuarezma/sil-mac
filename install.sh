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

# --dev: also install test tooling (pytest) via requirements-dev.txt,
# for contributors who want to run the test suite from the installed copy.
DEV_MODE=false
if [[ "$1" == "--dev" ]]; then
    DEV_MODE=true
fi

INSTALL_DIR="$HOME/.local/share/nexus-cli"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ_FILE="requirements.txt"
if [ "$DEV_MODE" = true ]; then
    REQ_FILE="requirements-dev.txt"
fi

echo "==> Bağımlılıklar ve izole Python ortamı hazırlanıyor..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/$REQ_FILE" --quiet

echo "==> Kaynak kodlar kopyalanıyor..."
cp -r "$SCRIPT_DIR/nexus" "$INSTALL_DIR/"
if [ "$DEV_MODE" = true ]; then
    cp -r "$SCRIPT_DIR/tests" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
fi

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

if [ "$DEV_MODE" = true ]; then
    echo -e "${PURPLE}Geliştirici modu:${NC} testleri çalıştırmak için:"
    echo -e "  ${CYAN}$INSTALL_DIR/venv/bin/python -m pytest $INSTALL_DIR${NC}\n"
fi
