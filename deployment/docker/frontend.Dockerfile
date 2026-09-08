# Phase 10A production frontend image (nginx).
# Build from repository root:
#   docker build -f deployment/docker/frontend.Dockerfile \
#     --build-arg VITE_API_BASE_URL=/api/v1 \
#     -t ai-forge-frontend:prod .

FROM node:26-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV NODE_ENV=production

RUN node ./scripts/build.mjs

FROM nginx:1.27-alpine AS runtime

COPY deployment/nginx/frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html
RUN chmod -R a-w /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
