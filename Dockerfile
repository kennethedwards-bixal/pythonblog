FROM python:3.8-slim-buster
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 8000
COPY . .

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000"]