# Самоподписанный сертификат для локальной демонстрации HTTPS.
# В продакшене используйте Let's Encrypt (certbot).
mkdir -p "$(dirname "$0")/certs"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$(dirname "$0")/certs/server.key" \
  -out "$(dirname "$0")/certs/server.crt" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
echo "Сертификат создан: $(dirname "$0")/certs/server.crt"
