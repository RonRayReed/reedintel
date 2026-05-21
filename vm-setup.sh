#!/bin/bash
set -e

# Run this script once on a fresh Ubuntu 22.04 VM to install Docker and deploy Reed Intel.
# Usage:  bash vm-setup.sh

echo "=== Installing Docker ==="
apt-get update -qq
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker
systemctl start docker

echo "=== Cloning repo ==="
cd /opt
git clone https://github.com/RonRayReed/reedintel.git
cd reedintel

echo "=== Creating .env ==="
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo ">>> Edit /opt/reedintel/.env and set DATABASE_PASSWORD, then re-run:"
  echo ">>>   cd /opt/reedintel && docker compose up -d --build"
  echo ""
else
  echo ".env already exists, skipping."
fi

echo "=== Done. Next step: edit .env then run: docker compose up -d --build ==="
