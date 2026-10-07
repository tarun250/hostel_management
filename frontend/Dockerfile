# syntax=docker/dockerfile:1
# ---- build stage: compile the React app ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- runtime stage: static files on unprivileged nginx (uid 101, port 8080) ----
FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime
USER root
RUN apk upgrade --no-cache
USER 101
ENV BACKEND_URL=http://backend:8000 \
    NGINX_ENVSUBST_FILTER=BACKEND_URL
COPY --chown=101:101 nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/nginx-health || exit 1
