# Pyalic: Python Advanced Licensing Server

Licensing server which allows you to manage access to your products

(Python module available on https://github.com/Yarosvet/Pyalic_py)

# Install server  in Docker

Firstly make an SSL certificate (and private key) for web server and place it to `/etc/ssl/lic_server/`.

```
/etc/ssl/
├── lic_server
│   ├── cert.crt
│   └── key.key

```

You can create self-signed one by executing next command with _YOUR_IP_ replaced with your external IP.

```shell
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/lic_server/key.key -out /etc/ssl/lic_server/cert.crt
openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes -keyout key.key -out cert.crt -subj "/CN=YOUR_IP" \
  -addext "subjectAltName=IP:YOUR_IP"
```

* If you are using domain name you should specify it instead of IP. In _subjectAltName_ set `DNS` value instead of `IP`

Then setup server using docker-compose

```shell
docker compose up
```

And you already have it launched! If you want to start it in detached mode add `-d` parameter:

```shell
docker compose -d up
```

# Run tests

There is a Dockerfile for running tests in Docker with needed services. So you should run following:

```shell
docker compose -f docker-compose.tests.yml up --build --exit-code-from test_lic_server
```

Or if you want to run tests without docker, you must install requirements from `src/tests/requirements.txt`, setup
PostgreSQL database and Redis server.
Pass credentials using environment variables (see `config.py` to get names)
Then tun `pytest` in `Pyalic_Server` directory.