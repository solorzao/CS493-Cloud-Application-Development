FROM python:3.7
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE ${PORT}
ENV GOOGLE_APPLICATION_CREDENTIALS='./hw8-containerize-solorzao-d820ed27e913.json'
CMD ["python", "main.py"]