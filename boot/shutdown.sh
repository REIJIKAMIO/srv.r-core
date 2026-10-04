#!/usr/bin/bash

dir=$(cd "$(dirname "$0")" && pwd)
cd $dir/../core/ui/
sudo docker compose down