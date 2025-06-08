# Use a slim Python base image
FROM python:3.10-slim

# Install system deps for Chrome & ChromeDriver
RUN apt-get update && apt-get install -y \
    wget gnupg2 unzip ca-certificates fonts-liberation \
    libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 libgbm-dev libasound2 && \
  # Install Google Chrome
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
  echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list && \
  apt-get update && \
  apt-get install -y google-chrome-stable && \
  # Install matching ChromeDriver
  CHROME_VER=$(google-chrome --version | sed -E 's/.* ([0-9]+)\..*/\1/') && \
  wget -q "https://chromedriver.storage.googleapis.com/${CHROME_VER}.0.XXXXXX/chromedriver_linux64.zip" \
    -O /tmp/chromedriver.zip && \
  unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
  rm /tmp/chromedriver.zip && chmod +x /usr/local/bin/chromedriver && \
  # Clean up apt
  apt-get purge -y wget gnupg2 unzip && apt-get autoremove -y && apt-get clean

# Create app directory
WORKDIR /app

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port and run via Gunicorn
ENV PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
