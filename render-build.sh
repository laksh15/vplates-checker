

#!/bin/bash
set -e

# Fixed Chromedriver version matching Chrome 114.x (adjust if needed)
CHROMEDRIVER_VERSION=114.0.5735.90

echo "Downloading Chromedriver version $CHROMEDRIVER_VERSION..."

wget -q --show-progress https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip

unzip -o chromedriver_linux64.zip
chmod +x chromedriver
sudo mv chromedriver /usr/local/bin/chromedriver

rm chromedriver_linux64.zip

echo "Chromedriver installed to /usr/local/bin/chromedriver"
