FROM node:24-alpine AS build
WORKDIR /app
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
ARG NEXT_PUBLIC_INFERENCE_URL=/api
ENV NEXT_PUBLIC_INFERENCE_URL=$NEXT_PUBLIC_INFERENCE_URL
RUN npm run build
FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build --chown=node:node /app ./
USER node
EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
