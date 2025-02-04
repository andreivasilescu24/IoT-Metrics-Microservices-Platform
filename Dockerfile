FROM python:latest
WORKDIR /adapter
COPY ./adapter.py /adapter
COPY ./requirements.txt /adapter
COPY ./.env /adapter
RUN pip install -r requirements.txt
CMD [ "python3", "adapter.py" ]