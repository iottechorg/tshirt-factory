# Stage 1: Build the Angular app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Make sure the build output directory is named correctly
RUN npm run build -- --configuration production --output-path=dist/tshirt-customizer 

# Stage 2: Serve the built app with Nginx
FROM nginx:alpine

# Copy the nginx config
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Verify the directory and copy
COPY --from=builder /app/dist/tshirt-customizer/browser/ /usr/share/nginx/html

# Verify copied files in nginx
RUN ls -l /usr/share/nginx/html

# Copy runtime env template and entrypoint script
COPY public/env.template.js /usr/share/nginx/html/env.js
COPY docker-entrypoint.d/50-set-env-js.sh /docker-entrypoint.d/50-set-env-js.sh
RUN chmod +x /docker-entrypoint.d/50-set-env-js.sh || true

# Ensure the app will load the generated env.js at runtime by injecting a script tag
RUN if grep -q "</head>" /usr/share/nginx/html/index.html 2>/dev/null; then \
			sed -i "s|</head>|  <script src=\"/env.js\"></script>\n</head>|" /usr/share/nginx/html/index.html || true; \
		fi

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]