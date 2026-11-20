FROM nginx:stable-alpine

COPY http.conf /opt/portfolio-nginx/http.conf
COPY https.conf /opt/portfolio-nginx/https.conf
COPY smalltalk-chat-location.conf /opt/portfolio-nginx/smalltalk-chat-location.conf
COPY chat-rate-limit.conf /etc/nginx/conf.d/00-chat-rate-limit.conf
COPY nginx-entrypoint.sh /usr/local/bin/portfolio-nginx-entrypoint

RUN chmod +x /usr/local/bin/portfolio-nginx-entrypoint

ENTRYPOINT ["/usr/local/bin/portfolio-nginx-entrypoint"]
