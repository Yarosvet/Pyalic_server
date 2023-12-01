FROM python:3.11-alpine as prod

WORKDIR /opt/pyAdvancedLic_Server

ADD app app
ADD requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

CMD gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app:app


FROM python:3.11-alpine as tests
WORKDIR /opt/pyAdvancedLic

ADD app app
ADD tests tests
ADD requirements.txt requirements.txt
ADD tests.requirements.txt tests.requirements.txt
ADD __init__.py __init__.py

RUN pip3 install -r requirements.txt
RUN pip3 install -r tests.requirements.txt

CMD "pytest"