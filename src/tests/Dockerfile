FROM python:3.11-alpine
# Context must be ../../
WORKDIR /opt/pyAdvancedLic

ADD src src/
ADD src/tests/run_tests.py run_tests.py

RUN pip3 install -r ./src/pyAdvancedLic_Server/requirements.txt
RUN pip3 install -r ./src/tests/requirements.txt

