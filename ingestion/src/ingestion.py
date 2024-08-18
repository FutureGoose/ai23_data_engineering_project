import os
import requests
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
# import psycopg2
from google.cloud import bigquery
import pendulum

app = FastAPI()
load_dotenv()


#This function fetches the weather data
def fetch_weather_data(api_url, api_key, location, date):
    params = {
        'key': api_key,
        'q': location,
        'date': date
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        print("Fetched data from API")
        return response.json()
    else:
        response.raise_for_status()


#This function unpacks the json and sends the data to postgres
# def json_to_psql(json_data):
    
#     conn = psycopg2.connect(
#         user=os.getenv('POSTGRES_USER'),
#         password=os.getenv('POSTGRES_PASSWORD'),
#         host='db',
#         port='5432',
#         database=os.getenv('POSTGRES_DB')
#     )
#     cur = conn.cursor()
    
#     for hour in json_data['hour']:
#         ingestion_timestamp = pendulum.now().format('YYYY-MM-DD:HH:mm:ss')
#         modified_timestamp = pendulum.from_format(json_data['location']['localtime'], 'YYYY-MM-DD HH:mm').format('YYYY-MM-DD:HH:mm:ss')
#         id_time_epoch = hour['time_epoch']
#         data = json.dumps(hour, indent=4)
#         cur.execute(
#             """
#             INSERT INTO RAW__WEATHERAPP (ingestion_timestamp, modified_timestamp, id, data)
#             VALUES (%s, %s, %s, %s)
#             """, (ingestion_timestamp, modified_timestamp, id_time_epoch, data)
#             )
#     conn.commit()
#     cur.close()
#     conn.close()
#     print(f'Inserted {len(json_data["hour"])} rows')

# This function unpacks the json and sends the data to BigQuery
def json_to_bigquery(json_data):
    client = bigquery.Client()
    table_id = "team-god.weather_data.raw_weatherapp"

    rows_to_insert = [
        {
            "ingestion_timestamp": pendulum.now().to_datetime_string(),
            "modified_timestamp": pendulum.from_format(json_data['location']['localtime'], 'YYYY-MM-DD HH:mm').to_datetime_string(),
            "id": hour['time_epoch'],
            "data": json.dumps(hour)
        }
        for hour in json_data['hour']
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f"Failed to insert rows: {errors}")
    print(f'Inserted {len(rows_to_insert)} rows')


@app.get("/")
def read_root():
    return "Welcome to our ingestion API"


@app.get("/ingestion")
def ingestion(location: str, date: str):
    API_URL = os.getenv('API_URL')
    API_KEY = os.getenv('API_KEY')

    formatted_data = json
    try:
        weather_data = fetch_weather_data(
            api_url=API_URL,
            api_key=API_KEY,
            location=location,
            date=date
            )
        formatted_data = {
            'location': weather_data['location'],
            'hour': weather_data['forecast']['forecastday'][0]['hour']
        }
    except requests.exceptions.RequestException as e:
        print(f'Error fetching data from API: {e}')
        raise HTTPException(status_code=500, detail="Error fetching data from API")

    # try:
    #     json_to_psql(formatted_data)
    # except Exception:
    #     print('Insert to Data Warehouse failed')

    try:
        json_to_bigquery(formatted_data)
    except Exception as e:
        print(f'Insert to BigQuery failed: {e}')
        raise HTTPException(status_code=500, detail="Insert to BigQuery failed")
