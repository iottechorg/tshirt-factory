FROM python:3.9-slim

ARG WEBAPP_PORT=5001
ENV WEBAPP_PORT=$WEBAPP_PORT

WORKDIR /app
COPY . /app



RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --force-reinstall werkzeug==2.1.2

# Use Gunicorn to serve the application in production
#CMD gunicorn -w 4 -b 0.0.0.0:$WEBAPP_PORT --log-level 'debug' app:app

CMD python app.py --host=0.0.0.0 --port=$WEBAPP_PORT
