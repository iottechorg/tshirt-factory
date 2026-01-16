#!/bin/sh
# Replace placeholder in env.js with the runtime API_URL environment variable
set -e
if [ -f /usr/share/nginx/html/env.js ]; then
  if [ -n "${API_URL}" ]; then
    sed -i "s|__API_URL__|${API_URL}|g" /usr/share/nginx/html/env.js
  else
    sed -i "s|__API_URL__|http://localhost:5001|g" /usr/share/nginx/html/env.js
  fi
fi
