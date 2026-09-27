#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
bash build_linux.sh

install_dir="${HOME}/.local/opt/andromeda-netkit"
applications_dir="${HOME}/.local/share/applications"
icons_dir="${HOME}/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$install_dir" "$applications_dir" "$icons_dir"
install -m 755 dist/AndromedaNetKit "$install_dir/AndromedaNetKit"
install -m 644 assets/network_diagnostics.png "$icons_dir/andromeda-netkit.png"

cat > "$applications_dir/andromeda-netkit.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=⚡ Andromeda NetKit
Comment=Network diagnostics and troubleshooting tools
Exec=${install_dir}/AndromedaNetKit
Icon=${icons_dir}/andromeda-netkit.png
Terminal=false
Categories=Network;Utility;
EOF
chmod 644 "$applications_dir/andromeda-netkit.desktop"
rm -f "${HOME}/.local/share/applications/network-diagnostics.desktop"

echo "Installed. Find '⚡ Andromeda NetKit' in your application menu."
