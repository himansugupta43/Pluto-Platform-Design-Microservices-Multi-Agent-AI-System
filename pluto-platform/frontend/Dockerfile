# --- Stage 1: Build the React application ---
FROM node:18-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package.json ./
COPY package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build the production-ready static files
RUN npm run build


# --- Stage 2: Serve the static files with Nginx ---
FROM nginx:stable-alpine

# Copy the built files from the 'builder' stage
COPY --from=builder /app/build /usr/share/nginx/html

# --- ADD THIS LINE ---
# Overwrite the default Nginx configuration with our custom one
COPY nginx.conf /etc/nginx/conf.d/default.conf
# ---------------------

# Nginx listens on port 80 by default
EXPOSE 80

# The command to start Nginx
CMD ["nginx", "-g", "daemon off;"]