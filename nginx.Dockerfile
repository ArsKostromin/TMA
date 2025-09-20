FROM nginx:1.25-alpine

# Установим модули brotli (dyn)
RUN apk add --no-cache nginx-mod-brotli && \
    mkdir -p /etc/nginx/modules-enabled

# Базовый конфиг nginx с подключением модулей
COPY nginx-main.conf /etc/nginx/nginx.conf

# Логи в stdout/stderr
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]


