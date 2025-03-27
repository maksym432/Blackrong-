#!/bin/bash
cd ~
mkdir -p Blackrong
curl -o ~/Blackrong/blackrong.py https://raw.githubusercontent.com/maksym432/Blackrong/main/blackrong.py
pip install colorama
python3 ~/Blackrong/blackrong.py