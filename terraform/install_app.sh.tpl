#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y ca-certificates curl git redis-server sudo

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf 2>/dev/null || true
if grep -q '^protected-mode' /etc/redis/redis.conf; then
  sed -i 's/^protected-mode .*/protected-mode no/' /etc/redis/redis.conf
else
  echo 'protected-mode no' >> /etc/redis/redis.conf
fi
systemctl enable redis-server
systemctl restart redis-server

id -u miche >/dev/null 2>&1 || useradd -m -s /bin/bash miche
echo "miche:${ssh_password}" | chpasswd
usermod -aG sudo,docker miche

mkdir -p /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/99-password-auth.conf <<'SSHEOF'
PasswordAuthentication yes
KbdInteractiveAuthentication yes
UsePAM yes
SSHEOF
systemctl restart ssh || systemctl restart sshd

APP_DIR="/opt/disponibilidad"
rm -rf "$${APP_DIR}"
mkdir -p "$${APP_DIR}"

git clone --depth 1 --branch main "${git_repo}" "$${APP_DIR}"

cat >"$${APP_DIR}/.env" <<ENVEOF
DJANGO_SECRET_KEY=terraform-bootstrap-change-me
DEBUG=False
ALLOWED_HOSTS=*
DB_HOST=${db_host}
DB_PORT=${db_port}
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
REDIS_URL=redis://172.17.0.1:6379/1
ENVEOF

cd "$${APP_DIR}"
docker compose build --pull
docker compose up -d

echo "Bootstrap finished" >> /var/log/disponibilidad-bootstrap.log
