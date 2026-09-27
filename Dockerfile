# EL MASRIA — static site on nginx (Coolify Dockerfile build pack)
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html
# COPY . تجلب ملفات البناء أيضًا — لا معنى لنشرها على الويب
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
