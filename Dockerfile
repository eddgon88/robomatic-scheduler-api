# Dockerfile
FROM python:3.8.10
COPY requirements.txt /app/requirements.txt
WORKDIR /app
ENV TZ=America/Santiago
RUN pip install -r requirements.txt && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
COPY . /app
ENTRYPOINT ["python"]
EXPOSE 5005
CMD ["run.py"]