#!/bin/bash
set -e

CHROMEDRIVER_VERSION=114.0.5735.90

echo "Downloading Chromedriver version $CHROMEDRIVER_VERSION..."

wget -q --show-progress https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip

unzip -o chromedriver_linux64.zip
chmod +x chromedriver

mkdir -p ./bin
mv chromedriver ./bin/

rm chromedriver_linux64.zip

echo "Chromedriver installed to ./bin/chromedriver"
