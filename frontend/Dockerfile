FROM node:13.12.0-alpine as build
LABEL description="Foodgram frontend" \
      version="1.0" \
      maintainer="Yandex Practicum" \
      deployer="https://github.com/TheSuncatcher222"
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD cp -r build result_build
