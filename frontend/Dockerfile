FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
# Same-origin API calls; nginx proxies /api to the backend (see nginx.conf).
RUN echo 'window.API_BASE = "";' > /usr/share/nginx/html/config.js
