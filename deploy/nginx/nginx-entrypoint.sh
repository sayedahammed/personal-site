#!/bin/sh
set -eu

cert_dir=/etc/letsencrypt/live/sayedahammed.com
if [ -s "$cert_dir/fullchain.pem" ] && [ -s "$cert_dir/privkey.pem" ]; then
    cp /opt/portfolio-nginx/https.conf /etc/nginx/conf.d/default.conf
else
    cp /opt/portfolio-nginx/http.conf /etc/nginx/conf.d/default.conf
fi

nginx -t
nginx -g "daemon off;" &
nginx_pid=$!

(
    while :; do
        sleep 30
        if [ -s "$cert_dir/fullchain.pem" ] && [ -s "$cert_dir/privkey.pem" ]; then
            cert_mtime=$(stat -c %Y "$cert_dir/fullchain.pem")
            if [ "$cert_mtime" != "${loaded_cert_mtime:-}" ] ||
                ! cmp -s /opt/portfolio-nginx/https.conf /etc/nginx/conf.d/default.conf; then
                cp /opt/portfolio-nginx/https.conf /etc/nginx/conf.d/default.conf
                if nginx -t; then
                    nginx -s reload
                    loaded_cert_mtime=$cert_mtime
                fi
            fi
        fi
    done
) &
watcher_pid=$!

shutdown() {
    kill -TERM "$watcher_pid"
    kill -QUIT "$nginx_pid"
    wait "$nginx_pid"
}

trap shutdown TERM INT
wait "$nginx_pid"
