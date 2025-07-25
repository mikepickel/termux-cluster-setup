#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Updating packages..."
pkg update -y && pkg upgrade -y

echo "📥 Installing system dependencies..."
pkg install -y git curl clang cmake make python rust ninja \
               autoconf automake libtool python-numpy python-torch

echo "⚙️ Installing rustup..."
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.profile

echo "🐍 Upgrading Python build tools..."
pip install --upgrade pip setuptools wheel maturin

echo "📦 Installing Python packages..."
pip install transformers flask requests safetensors accelerate 

echo "🔐 Setting up SSH authorized key..."
mkdir -p ~/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC9bhbOSiREm8kavPvR5OSMWkSONLo/wN7MSflbb10wtAUrvxoz0JTvC+6mb7wGOTVmuDc+gU77O1hl18
E8CE0Y7asVplYy9W4FDsIdkGBOcqrL1bxgRkWK+jnSL4ztbrSXLXervntDEcyJoN3tBb50ehJMuqFFW46QwO+sg9eyVId6UL3KO+joqI7Tv62lVYOWB9R3
dvO6k1PI7nSFKutAp9fq1AzshaTGrYBwHV9+wdyj7lQ3D9GNUXaROzLTGeQ4lJOwVQLqs7en9A6lzH/sbyJtJ1uVfKiyKyN4rbSv9os2bX5UNbwZF+wGao
s5VKaK37B3QFOTahhO1hhg/9wqQcAdc7NFH9oHPUZ5w6n8Xv8nPyT267fR/zdwxJCt5IsW+fijNX70koRBIIjO/6k6eMTkGWVT8EN4xFocD1x3Oq50/JhW
jgKKUkqRz+jPAh5IYqvgORwsGgGinQq4plb/N3cBuUmvpoLztwWDSvWEsQFglSdWWh/Y9q3QgG/TwpCQOlRxHP1AinbuAQdwtgGqJfbQlzWWYffq0DUC/U
fF/lCi1SXPUpbS97TjuZYYhYZTzUtHQ72W9MJdenrFOukHyRlGH3knR19OvVg/kSwL7sU7rFNqi37suGasLbjOE9VX0QWB0s8p8G7pcK2d856MYo/Y6hlvvq5rZfwlj++t9Q== phone-cluster-deployment
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

echo "✅ Setup complete! Run: source ~/.profile or restart Termux"
