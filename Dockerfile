FROM python:3.12-slim

WORKDIR /usr/src/app

RUN groupadd -g 442 app && \
    useradd -u 442 -g 442 -M -d /usr/src/app -c 'app user' app && \
    chown -R app:app /usr/src/app

COPY . /usr/src/app

RUN apt-get update && \
    apt-get install -y gcc && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get autoremove --purge -y gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER app
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
CMD ["python", "-O", "-m", "sunbot"]
