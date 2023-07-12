# Python Advanced Licensing Server

Licensing server which allows you to manage access to your products

# Install python API wrapper
Install package using `pip` from this GitHub repository
```shell
pip install git+https://github.com/Yarosvet/pyAdvancedLic#subdirectory=src/pyAdvanced_license
```

# Python example
```python
from pyAdvanced_license import LicenseManager
import time

lm = LicenseManager("https://LICENSE_SERVER_URL.ORG", ssl_public_key='./trusted_cert.pem')


def my_program():
    print("Access granted!")
    time.sleep(30)


key = input("Enter your license key: ")
if lm.check_key(key):
    my_program()
    lm.end_session()
else:
    print("Access denied:", lm.status)
```

# Install server  in Docker

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

Then setup server using docker-compose

```shell
docker compose up
```

And you already have it launched! If you want to start it in detached mode add `-d` parameter:

```shell
docker compose -d up
```