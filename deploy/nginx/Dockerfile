FROM nginx:stable-alpine

COPY http.conf /opt/portfolio-nginx/http.conf
COPY https.conf /opt/portfolio-nginx/https.conf
COPY nginx-entrypoint.sh /usr/local/bin/portfolio-nginx-entrypoint

RUN chmod +x /usr/local/bin/portfolio-nginx-entrypoint

ENTRYPOINT ["/usr/local/bin/portfolio-nginx-entrypoint"]
