FROM node:20-alpine AS deps

WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci

FROM node:20-alpine AS builder

WORKDIR /app/apps/web
ARG NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
COPY --from=deps /app/apps/web/node_modules ./node_modules
COPY apps/web ./
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app/apps/web
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

COPY --from=builder /app/apps/web/package*.json ./
COPY --from=builder /app/apps/web/node_modules ./node_modules
COPY --from=builder /app/apps/web/.next ./.next
COPY --from=builder /app/apps/web/next.config.mjs ./

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000 || exit 1

CMD ["npm", "run", "start"]
