# Build stage
FROM node:18 AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies with memory limit
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm install

# Copy source files (excluding node_modules)
COPY . .
RUN rm -rf node_modules
RUN npm install

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
