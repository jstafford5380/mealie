FROM node:26@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac

RUN npm install --global pnpm@12.20.0
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend ./
COPY dev/aspire/empty.env /opt/empty.env

CMD ["pnpm", "exec", "nuxt", "dev", "--host", "0.0.0.0", "--port", "3000", "--no-fork", "--dotenv", "/opt/empty.env"]
