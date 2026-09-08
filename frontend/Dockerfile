FROM node:20-slim AS build

WORKDIR /app
COPY package.json ./
COPY package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Railway supplies PORT at runtime; docker-compose keeps the defaults below.
# The official Nginx entrypoint expands this template before starting Nginx.
ENV PORT=80
ENV BACKEND_UPSTREAM=backend:8000
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80
