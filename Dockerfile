FROM python:3.10.9-slim-bullseye

WORKDIR /usr/src/app

RUN groupadd -g 442 app && \
    useradd -u 442 -g 442 -M -d /usr/src/app -c 'app user' app && \
    chown -R app:app /usr/src/app

COPY . /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

USER app
CMD ["python", "-m", "sunbot"]
