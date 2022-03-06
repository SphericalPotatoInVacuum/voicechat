FROM python:3.9.10

RUN apt update && apt install -y portaudio19-dev python3-pyaudio

WORKDIR /server

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/server.py src/protocol.py ./

ENTRYPOINT ["python3", "server.py"]
