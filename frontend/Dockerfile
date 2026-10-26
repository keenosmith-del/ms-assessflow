FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ARG VITE_ENTRA_TENANT_ID
ARG VITE_ENTRA_CLIENT_ID
ARG VITE_ENTRA_SCOPE
ENV VITE_API_URL=$VITE_API_URL VITE_ENTRA_TENANT_ID=$VITE_ENTRA_TENANT_ID VITE_ENTRA_CLIENT_ID=$VITE_ENTRA_CLIENT_ID VITE_ENTRA_SCOPE=$VITE_ENTRA_SCOPE
RUN npm run build
FROM nginxinc/nginx-unprivileged:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
