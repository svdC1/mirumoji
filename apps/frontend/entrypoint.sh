#!/bin/sh
# Entrypoint to provision TLS at container runtime
# Expects `HOST_LAN_IP` env variable to build the server certificate
#
# A persistent local CA (kept in a volume across restarts) signs a short-lived
# server certificate for the current LAN IP. Installing the CA once per device
# makes the origin fully trusted, which browsers require before they register
# the service worker (and therefore before the PWA is installable). The CA is
# served at /mirumoji-ca.crt for that one-time install
set -e

CERT_DIR=/etc/nginx/ssl
CA_KEY="$CERT_DIR/ca.key"
CA_CRT="$CERT_DIR/ca.crt"
CERT_KEY="$CERT_DIR/server.key"
CERT_CRT="$CERT_DIR/server.crt"
CERT_CSR="$CERT_DIR/server.csr"
CERT_EXT="$CERT_DIR/server.ext"
CERT_CHAIN="$CERT_DIR/fullchain.crt"
IP=${HOST_LAN_IP:-127.0.0.1}  # fallback to 127.0.0.1 if not provided

mkdir -p "$CERT_DIR"

# --- Local CA (generated once, persisted in the certs volume) ---
if [ ! -f "$CA_KEY" ] || [ ! -f "$CA_CRT" ]; then
    echo "Generating Mirumoji Local CA"
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout "$CA_KEY" \
        -out "$CA_CRT" \
        -subj "/CN=Mirumoji Local CA/O=Mirumoji" \
        -addext "basicConstraints=critical,CA:TRUE" \
        -addext "keyUsage=critical,keyCertSign,cRLSign"
fi

# --- Server certificate (regenerated when the IP changes or it nears expiry) ---
# Apple requires leaf certificates to be valid for at most 825 days, so the
# leaf is short-lived while the CA (what devices actually trust) is not
needs_leaf=0
if [ ! -f "$CERT_KEY" ] || [ ! -f "$CERT_CRT" ]; then
    needs_leaf=1
elif ! openssl x509 -in "$CERT_CRT" -noout -ext subjectAltName 2>/dev/null | grep -q "IP Address:$IP"; then
    needs_leaf=1
elif ! openssl x509 -in "$CERT_CRT" -noout -checkend 2592000 >/dev/null 2>&1; then
    # Expires within 30 days
    needs_leaf=1
elif ! openssl verify -CAfile "$CA_CRT" "$CERT_CRT" >/dev/null 2>&1; then
    # Not signed by the current CA (e.g. a leftover self-signed cert)
    needs_leaf=1
fi

if [ "$needs_leaf" = "1" ]; then
    echo "Generating Server Certificate For IP: $IP"
    openssl req -nodes -newkey rsa:2048 \
        -keyout "$CERT_KEY" \
        -out "$CERT_CSR" \
        -subj "/CN=$IP"
    cat > "$CERT_EXT" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:$IP,IP:127.0.0.1,DNS:localhost
EOF
    openssl x509 -req -days 825 \
        -in "$CERT_CSR" \
        -CA "$CA_CRT" \
        -CAkey "$CA_KEY" \
        -CAcreateserial \
        -out "$CERT_CRT" \
        -extfile "$CERT_EXT"
    rm -f "$CERT_CSR" "$CERT_EXT"
fi

# Serve the full chain, and expose the CA for the one-time device install
cat "$CERT_CRT" "$CA_CRT" > "$CERT_CHAIN"
cp "$CA_CRT" /usr/share/nginx/html/mirumoji-ca.crt

echo "Starting Nginx ..."
exec nginx -g "daemon off;"
