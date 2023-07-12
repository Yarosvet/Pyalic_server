# pyAdvancedLic - license server on Python

Licensing server which allows you to manage access to your products

# Install in Docker and run

Firstly make an SSL certificate (and private key) for web server and place it to `/etc/ssl/lic_server/`.

```
/etc/ssl/
├── lic_server
│   ├── cert.crt
│   └── key.key

```

You can create self-signed one by executing next command and typing your IP or domain in `Common name` row:

```shell
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/lic_server/key.key -out /etc/ssl/lic_server/cert.crt
```

Then set up server itself using docker-compose

```shell
docker compose up
```

And you already have it launched! If you want to start it in detached mode add `-d` parameter:

```shell
docker compose -d up
```