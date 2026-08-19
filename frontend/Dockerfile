# --- Build stage ---
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Vite env vars are baked in at build time, not read at container runtime --
# pass a real backend URL here for anything beyond local docker-compose
# (where the default localhost:8000 fallback in src/api.js already works,
# since the browser hits a host-mapped port either way).
ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# --- Serve stage ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
