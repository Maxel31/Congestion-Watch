FROM node:22-alpine
WORKDIR /app
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install
COPY frontend/ ./
CMD ["yarn", "dev", "--host"]
