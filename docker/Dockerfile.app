FROM python:3.8.10
# RUN ["apt-get", "update"]
WORKDIR /app
COPY . /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD [ "python3","./app_auth.py" ]
