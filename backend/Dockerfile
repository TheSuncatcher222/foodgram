FROM python:3.11
LABEL description="Foodgram backend" \
      version="1.0" \
      maintainer="Altair21817" \
      deployer="https://github.com/Altair21817"
RUN pip install --upgrade pip
RUN pip install gunicorn==20.1.0
WORKDIR /foodgram
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]
