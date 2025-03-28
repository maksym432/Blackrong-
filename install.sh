#!/bin/bash
cd ~
rm -rf Blackrong 2>/dev/null
mkdir Blackrong && cd Blackrong

echo "[+] Downloading latest version..."
wget -q https://raw.githubusercontent.com/maksym432/Blackrong/main/blackrong.py

echo "[+] Installing dependencies..."
pip install --quiet colorama

echo "[+] Starting..."
python3 blackrong.py