#!/usr/bin/env bash
# Script chạy PTIT MQTT Monitor trên Linux / Raspberry Pi OS

cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "[LỖI] Chưa cài đặt python3 trên hệ thống!"
    echo "Cài đặt bằng lệnh: sudo apt update && sudo apt install python3 python3-pip python3-tk -y"
    exit 1
fi

if command -v uv &> /dev/null; then
    uv run --with paho-mqtt --with Pillow app.py
else
    python3 -m pip install -q paho-mqtt Pillow 2>/dev/null
    python3 app.py
fi

