# Stage 1: Build the Angular app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Set the environment variables for the build
ARG API_URL
ENV API_URL=$API_URL

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

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]