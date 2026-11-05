import json
import re
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Configuration
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
DATABASE_NAME = os.getenv("MYSQL_DATABASE")

JSON_FILE = BASE_DIR / "dataset" / "sample_data_for_assignment.json"


# Create MySQL engine
def create_mysql_engine():

    required_variables = {
        "MYSQL_USER": MYSQL_USER,
        "MYSQL_PASSWORD": MYSQL_PASSWORD,
        "MYSQL_HOST": MYSQL_HOST,
        "MYSQL_PORT": MYSQL_PORT,
        "MYSQL_DATABASE": DATABASE_NAME,
    }

    missing = [
        name
        for name, value in required_variables.items()
        if value is None or value == ""
    ]

    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        database=DATABASE_NAME,
    )

    return create_engine(connection_url)


# Read JSON and create DataFrame
def load_json_data(file_path):

    with file_path.open("r", encoding="utf-8") as file:
        json_data = json.load(file)

    df = pd.DataFrame(data=json_data["data"], columns=json_data["cols"])

    return df


# Insert DataFrame into MySQL
def insert_into_mysql(df, engine):

    df.to_sql(name="json_to_sql_table", con=engine, if_exists="replace", index=False)

    print("\nData successfully inserted into MySQL.")


# Retrieve data from MySQL into DataFrame
def retrieve_from_mysql(engine):

    query = text("SELECT * FROM json_to_sql_table")

    with engine.connect() as connection:
        df = pd.read_sql(query, con=connection)

    print("\nData retrieved from MySQL:")
    print(df.to_string(index=False))

    return df


# Normalize email addresses
def normalize_emails(df):

    df["email"] = df["email"].str.rsplit("@", n=1).str[0] + "@gmail.com"

    return df


# Convert postalZip into integers
def clean_postal_zip(df):

    df["postalZip"] = (
        df["postalZip"].astype(str).str.replace(r"\D", "", regex=True).astype("int64")
    )

    return df


# Encode phone numbers
def encode_phone_number(phone):

    digits = re.sub(r"\D", "", str(phone))
    encoded = ""

    for i in range(0, len(digits) - 1, 2):

        pair = int(digits[i : i + 2])

        if pair < 65:
            encoded += "O"
        else:
            encoded += chr(pair)

    return encoded


def encode_phone_column(df):

    df["phone"] = df["phone"].apply(encode_phone_number)

    df.rename(columns={"phone": "coded_phone_number"}, inplace=True)

    return df


# Main function
def main():

    if not JSON_FILE.exists():
        raise FileNotFoundError(f"JSON file not found: {JSON_FILE}")

    df = load_json_data(JSON_FILE)

    print("Initial DataFrame:")
    print(df.to_string(index=False))

    engine = create_mysql_engine()

    try:
        insert_into_mysql(df, engine)

        df = retrieve_from_mysql(engine)

        df = normalize_emails(df)
        df = clean_postal_zip(df)
        df = encode_phone_column(df)

        print("\nFinal Transformed DataFrame:")
        print(df.to_string(index=False))

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
