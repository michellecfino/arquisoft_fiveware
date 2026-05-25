#!/bin/bash
cd /opt/agregador_costos
sudo systemctl start mongod 2>/dev/null
pkill -f "manage.py runserver" 2>/dev/null
nohup python3 manage.py runserver 0.0.0.0:8002 > /tmp/agregador.log 2>&1 &
echo "✅ Agregador iniciado en puerto 8002"
