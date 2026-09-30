#!/usr/bin/env bash
# Run the repo's nginx.conf in a throwaway container and prove the redirect
# behaviour, WITHOUT touching the live site.
#
#   bash _tools/nginx_redirect_test.sh <path-to-nginx.conf> [port]
#
# Checks:
#   1. nginx -t on the real config
#   2. GET /            -> 200 and NO redirect loop (the whole point of keying
#                          the /index.html collapse on $request_uri)
#   3. GET /index.html  -> 301 with a RELATIVE Location (/), so the visitor
#                          keeps their scheme and port
#   4. the query-string form behaves the same
#   5. the pre-existing legacy WordPress redirect still works, also relative
#   6. following the redirect lands 200 on the SAME origin (proves no scheme/port
#      downgrade) -- this is the check that fails when absolute_redirect is on
#   7. an unknown path still 404s
set -euo pipefail

CONF="${1:?usage: nginx_redirect_test.sh <nginx.conf> [port]}"
PORT="${2:-18080}"
NAME="ngx-redirect-test"
HTML_DIR=/tmp/ngx-redirect-test/html

mkdir -p "$HTML_DIR/services"
printf '<h1>home</h1>\n' > "$HTML_DIR/index.html"
printf '<h1>services</h1>\n' > "$HTML_DIR/services/index.html"
printf '<h1>not found</h1>\n' > "$HTML_DIR/404.html"

cleanup() { sudo docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

sudo docker rm -f "$NAME" >/dev/null 2>&1 || true
sudo docker run -d --name "$NAME" -p "${PORT}:80" \
  -v "$(readlink -f "$CONF")":/etc/nginx/conf.d/default.conf:ro \
  -v "$HTML_DIR":/usr/share/nginx/html:ro \
  nginx:alpine >/dev/null

# wait for the port instead of a blind sleep
for _ in $(seq 1 40); do
  if curl -s -o /dev/null "http://127.0.0.1:${PORT}/"; then break; fi
  sleep 0.25
done

BASE="http://127.0.0.1:${PORT}"
LEGACY="/%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA/"   # /الخدمات/ percent-encoded

echo "=== syntax ==="
sudo docker exec "$NAME" nginx -t 2>&1 | tail -2

echo
echo "=== headers ==="
for path in "/index.html" "/index.html?x=1" "$LEGACY"; do
  printf 'GET %-28s ' "$path"
  curl -s -o /dev/null -D - "${BASE}${path}" 2>/dev/null \
    | tr -d '\r' | grep -iE "^HTTP/|^location:" | tr '\n' ' '
  echo
done

echo
echo "=== statuses ==="
code() { curl -s -o /dev/null -w '%{http_code}' "$1"; }
printf 'GET /                     -> %s\n' "$(code "${BASE}/")"
printf 'GET /missing.html         -> %s\n' "$(code "${BASE}/missing.html")"

echo
echo "=== follow the redirect (must land 200 on the SAME origin) ==="
curl -s -o /dev/null -L \
  -w 'GET -L /index.html          -> %{http_code}  final=%{url_effective}  redirects=%{num_redirects}\n' \
  "${BASE}/index.html"
curl -s -o /dev/null -L \
  -w "GET -L ${LEGACY} -> %{http_code}  final=%{url_effective}  redirects=%{num_redirects}\n" \
  "${BASE}${LEGACY}"
