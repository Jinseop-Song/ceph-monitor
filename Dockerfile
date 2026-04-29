FROM python:3.10

LABEL maintainer=jinseop.song@lunit.io

WORKDIR /app

COPY ceph_monitor_v2 /app

COPY requirements.txt /app

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

ENTRYPOINT ["python3", "-u", "main.py"]