FROM nginx:stable-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config and landing page
COPY nginx.conf /etc/nginx/nginx.conf
COPY html/ /usr/share/nginx/html/

EXPOSE 80
