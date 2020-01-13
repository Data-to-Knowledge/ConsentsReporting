FROM python:3.7-slim

COPY requirements.txt util.py process_data.py ts_processing.py reporting_tables.py reporting_tables_ts.py main.py ./

ENV TZ='Pacific/Auckland'

RUN apt-get update && apt-get install -y unixodbc-dev gcc g++

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py", "parameters.yml"]
