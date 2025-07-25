#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Updating packages..."
pkg update -y && pkg upgrade -y

echo "📥 Installing system dependencies..."
pkg install -y git curl clang cmake make python rust ninja \
               autoconf automake libtool python-numpy

echo "⚙️ Installing rustup..."
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.profile

echo "🐍 Upgrading Python build tools..."
pip install --upgrade pip setuptools wheel maturin

echo "📦 Installing Python packages..."
pip install torch transformers flask requests safetensors

echo "✅ Setup complete! Run: source ~/.profile or restart Termux"
