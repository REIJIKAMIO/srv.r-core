#!/usr/bin/bash

dir=$(cd "$(dirname "$0")" && pwd)
cd $dir/../core/
sudo docker compose up -d