#!/bin/sh
# Entrypoint to generate SSL Certificate at Container Runtime
set -e

CERT_DIR=/etc/nginx/ssl
CERT_KEY="$CERT_DIR/server.key"
CERT_CRT="$CERT_DIR/server.crt"
IP=${HOST_LAN_IP:-127.0.0.1}  # fallback to 127.0.0.1 if not provided

mkdir -p "$CERT_DIR"

# Generate a self-signed certificate with the current IP in the SAN
echo "Generating SSL certificate for IP: $IP"

openssl req -x509 -nodes -days 7 -newkey rsa:2048 \
    -keyout "$CERT_KEY" \
    -out "$CERT_CRT" \
    -subj "/CN=$IP" \
    -addext "subjectAltName=IP:$IP"

echo "Starting Nginx..."
exec nginx -g "daemon off;"
