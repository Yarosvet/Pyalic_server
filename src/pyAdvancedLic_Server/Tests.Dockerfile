FROM python:3.11-alpine
WORKDIR /opt/pyAdvancedLic

ADD app app
ADD tests tests
ADD requirements.txt requirements.txt
ADD tests.requirements.txt tests.requirements.txt
ADD __init__.py __init__.py

RUN pip3 install -r requirements.txt
RUN pip3 install -r tests.requirements.txt

CMD "pytest"