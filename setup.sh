#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Updating packages..."
pkg update -y && pkg upgrade -y

echo "📥 Installing system dependencies..."
pkg install -y python curl clang cmake make ninja wget \
               autoconf automake libtool rust python-numpy python-torch

echo "⚙️ Installing rustup..."
if [ ! -d "$HOME/.cargo" ]; then
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    source $HOME/.cargo/env
    rustup default stable
fi

echo "🐍 Upgrading Python build tools..."
pip install --upgrade setuptools wheel maturin

echo "📦 Installing Python packages..."
pip install transformers flask requests safetensors accelerate 

mkdir -p ~/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJYvZ6/H3+g9jywjO6Fk5Vt5A+w3OVHHfgBkzAhvVXVARao9FcYoggZvY2nx06EY5Fp+G8EgzxZyUBN1c2VLdrVh8/8gEy7hU9W/LbXvMivWMAXXeVtAvvlNdREbIAH11zcYA9arKvwGRpedXPbdJBkcd1Ya5xP6kDMSTgWVK8fxs9P+977HYyHoTRvxSn0c9GhY5amVmSiPhC4CnQvtCKrinyk1y47lrDafNB2yQQ95k9pwRijuBMfXVUHxIRSXt2yL48Uy26P7EAMxngZ1qcpvOpfAMHp+zgRiYbIEHIuo8q3QjZ7DNj973UelFuUMN5LMNjs0WnoV238MXGfmnf5laj9BoCyvP1RzvnjkDQC8eqMntlMYF9jbWBqsqvE+6t2/jnBQMHf1bXd2/h7iP1k4bDDShtSrivJqkQ4rD+E1a7CvrNk/Bwo7CbJ5rLfDT3xSQoG98h34Dut3pcECPc0btkfH9zGjEh9M98YR9So6KSAFYCR4PMiow1QxP58MVmfPvgDzaAZxoSs71R3rSIygxMwtCFpqqSvFQMgtE6H8L5fFXXPsZtDX+BQi9Ig3ETcJe0I9f7QwE1V2YmmzCSimw4nUgfYPnlsajmFmrQ0RH0xj0zANS3quBUtwLdBJMNfrP0kZTDupkCHtVkpFGTrQvPvfzD6OoJI5O+ydFw8Q== phone-cluster-key' > ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
sshd


echo "✅ Setup complete! Run: source ~/.profile or restart Termux"
