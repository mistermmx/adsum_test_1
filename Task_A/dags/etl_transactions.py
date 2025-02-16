import base64
import json

import boto3
import pandas as pd
import psycopg2
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from sqlalchemy import create_engine

# Constants
GOOGLE_DRIVE_BASE_URL = r'https://drive.google.com/uc?id='


def encrypt_data(data: str) -> str:
    """
    Encrypts a string using Fernet encryption and encodes it for JSON compatibility.
    :param data: The data to encrypt (string format).
    :return: Base64-encoded encrypted data as a string.
    """
    key = Variable.get("FERNET_KEY")
    cipher = Fernet(key.encode())
    encrypted_data = cipher.encrypt(data.encode())  # Encrypt data
    return base64.b64encode(encrypted_data).decode()  # Encode bytes to Base64 string


def decrypt_data(data: str) -> str:
    """
    Decrypts a Base64-encoded encrypted string using Fernet encryption.
    :param data: The Base64-encoded encrypted string to decrypt.
    :return: Original decrypted data (string format).
    """
    key = Variable.get("FERNET_KEY")
    cipher = Fernet(key)
    encrypted_data = base64.b64decode(data.encode())  # Decode Base64 string to bytes
    return cipher.decrypt(encrypted_data).decode()  # Decrypt bytes to original string


def get_connection_params(**context):
    """
    Fetch database credentials from AWS Secrets
    """
    secret_name = "adsum_db_credentials_2"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    connection_params = get_secret_value_response['SecretString']
    # Encrypt connection_params before passing through to XCOM
    encrypted_connection_params = encrypt_data(connection_params)
    context['ti'].xcom_push(key='connection_params', value=encrypted_connection_params)


# Utility Functions
def convert_to_float(dataframe):
    """Converts the 'amount' column to float format."""
    dataframe['amount'] = pd.to_numeric(dataframe['amount'], errors='coerce')
    return dataframe


def normalize_dates(dataframe):
    """Normalizes the 'transaction_date' column to date format (YYYY-MM-DD)."""
    dataframe['transaction_date'] = pd.to_datetime(dataframe['transaction_date'], format='mixed', dayfirst=True,
                                                   errors='raise').dt.strftime('%Y-%m-%d')
    return dataframe


def remove_duplicate_transactions(dataframe):
    """Removes duplicate transactions based on 'transaction_id'"""
    return dataframe.drop_duplicates(subset=['transaction_id'], keep='first')


# Task Functions
def create_table(**context):
    sql_query = """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        transaction_id VARCHAR(50) UNIQUE NOT NULL,
        user_id INT NOT NULL,
        amount FLOAT NOT NULL,
        transaction_date DATE NOT NULL
    );
    """
    encrypted_connection_params = context['ti'].xcom_pull(key='connection_params')
    decrypted_connection_params = decrypt_data(encrypted_connection_params)
    connection_params = json.loads(decrypted_connection_params)
    with psycopg2.connect(**connection_params) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            connection.commit()


def fetch_financial_data(**context):
    """
    Fetches financial data from a specific Google Drive URL and loads it into a pandas DataFrame.
    The resulting DataFrame will be stored in XCom for use by other tasks.
    """
    url = r'https://drive.google.com/file/d/1jORbN_ETnT92S_tIrYqYBLJ37aEyrShV/view?usp=sharing'
    downloadable_url = GOOGLE_DRIVE_BASE_URL + url.split('/')[-2]
    dataframe = pd.read_csv(downloadable_url)

    # Push the dataframe to XCom for the next tasks
    encrypted_dataframe = encrypt_data(dataframe.to_json())
    context['ti'].xcom_push(key='raw_dataframe', value=encrypted_dataframe)


def transform_financial_data(**context):
    """
    Transforms the loaded financial data by cleaning and normalizing it.
    """
    # Retrieve DataFrame from XCom

    decrypted_dataframe = decrypt_data(context['ti'].xcom_pull(key='raw_dataframe'))
    raw_dataframe = pd.read_json(decrypted_dataframe)
    # connection_params = json.loads(decrypted_connection_params)
    # Apply transformations
    dataframe = convert_to_float(raw_dataframe)
    dataframe = normalize_dates(dataframe)
    dataframe = remove_duplicate_transactions(dataframe)

    # Split the data into valid and blank rows
    valid_data = dataframe.dropna()

    # Encrypt data before passing to XCOM
    encrypted_data = encrypt_data(valid_data.to_json())
    context['ti'].xcom_push(key='transformed_dataframe', value=encrypted_data)


def fetch_sql_transactions(**context):
    """
    Fetch records from PostgreSQL and load into a pandas DataFrame, then subtract those SQL records from the new data.
    This way we only ever add new data to the SQL table.
    :param context:
    :return:
    """
    decrypted_dataframe = decrypt_data(context['ti'].xcom_pull(key='transformed_dataframe'))
    transformed_dataframe = pd.read_json(decrypted_dataframe)
    connection_params = json.loads(decrypt_data(context['ti'].xcom_pull(key='connection_params')))
    con_str = f'postgresql://{connection_params["user"]}:{connection_params["password"]}@{connection_params["host"]}:{connection_params["port"]}/{connection_params["dbname"]}'
    engine = create_engine(con_str)
    sql_query = """SELECT transaction_id,
                          user_id,
                          amount,
                          transaction_date 
                   FROM transactions"""
    sql_dataframe = pd.read_sql_query(sql_query, engine)
    # Ensure transformed_dataframe contains only unique records not present in sql_dataframe
    final_dataframe = transformed_dataframe[
        ~transformed_dataframe['transaction_id'].isin(sql_dataframe['transaction_id'])
    ]
    encrypted_data = encrypt_data(final_dataframe.to_json())
    context['ti'].xcom_push(key='transformed_dataframe', value=encrypted_data)


def load_data(**context):
    """
    Inserts the cleaned transactions into the 'transactions' PostgreSQL table.
    """
    # Retrieve transformed Da taFrame from XCom
    decrypted_data = decrypt_data(context['ti'].xcom_pull(key='transformed_dataframe'))
    dataframe = pd.read_json(decrypted_data)
    connection_params = json.loads(decrypt_data(context['ti'].xcom_pull(key='connection_params')))
    con_str = f'postgresql://{connection_params["user"]}:{connection_params["password"]}@{connection_params["host"]}:{connection_params["port"]}/{connection_params["dbname"]}'
    engine = create_engine(con_str)
    dataframe.to_sql('transactions', engine, if_exists="append", index=False)


# DAG Definition
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}

dag = DAG(
    'financial_data_pipeline_sql_encrypted',
    default_args=default_args,
    description='A DAG for fetching, transforming, and loading financial data.',
    schedule_interval='0 0 * * *',
)

# Task Definitions
get_connection_params_task = PythonOperator(
    task_id='get_connection_params',
    python_callable=get_connection_params,
    provide_context=True,
    dag=dag,
)

create_table_task = PythonOperator(
    task_id='create_table',
    python_callable=create_table,
    provide_context=True,
    dag=dag,
)

fetch_data_task = PythonOperator(
    task_id='fetch_data',
    python_callable=fetch_financial_data,
    provide_context=True,
    dag=dag,
)

transform_data_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_financial_data,
    provide_context=True,
    dag=dag,
)

fetch_sql_transactions_task = PythonOperator(
    task_id='fetch_sql_transactions',
    python_callable=fetch_sql_transactions,
    provide_context=True,
    dag=dag,
)

load_data_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    provide_context=True,
    dag=dag,
)

# Task Dependencies
get_connection_params_task >> create_table_task >> fetch_data_task >> transform_data_task >> fetch_sql_transactions_task >> load_data_task
