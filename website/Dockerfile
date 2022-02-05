FROM ubuntu:20.04

MAINTAINER Anna Nikiforovskaya "nikiannanik@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

#ENV STATIC_URL /static
#ENV STATIC_PATH /app/static

#ENTRYPOINT [ "python3" ]

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
