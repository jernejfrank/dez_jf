"""Injecting local csv data into a postgres database."""

import pandas as pd
import sqlalchemy as sa
from pandas.io.parsers.readers import TextFileReader
from sqlalchemy import Engine, create_engine


def create_connection(url: str) -> Engine:
    """Sqlalchemy engine connecting to a db."""
    return create_engine(url)


def create_pd_iterator_from_csv(file: str, batch: int = 100000) -> TextFileReader:
    """Loads csv into a pd dataframe and creates iterator for batch injection."""
    df_iter = pd.read_csv(file, iterator=True, chunksize=batch)
    return df_iter


def init_table(table_name: str, columns: pd.DataFrame, conn: Engine) -> None:
    """Creates new table in postgres db. Drops existing table."""
    columns.to_sql(name=table_name, con=conn, if_exists="replace")


def convert_columns_to_datetime(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Converts dataframe columns to datetime."""
    if "yellow" in table_name:
        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    elif "green" in table_name:
        df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
        df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)
    return df


def main(table_name: str, file: str, db_url: str, reset_table: bool = False) -> None:
    """Injecting csv data into postgres db pipeline."""
    df_iter = create_pd_iterator_from_csv(file)
    conn = create_connection(db_url)

    total_rows = 1369766  # 476386
    current_rows = 0
    for i, batch in enumerate(df_iter):
        batch = convert_columns_to_datetime(batch, table_name=table_name)

        if i == 0 and (reset_table or not sa.inspect(conn).has_table(table_name)):
            init_table(table_name, batch.head(n=0), conn)

        batch.to_sql(name=table_name, con=conn, if_exists="append")
        current_rows += batch.shape[0]
        print(f"Processed {current_rows} / {total_rows} rows")

    print()


if __name__ == "__main__":
    URL = "postgresql://root:root@localhost:5432/ny_taxi"
    FILE = "yellow_tripdata_2021-01.csv"
    NAME = "yellow_taxi_data"

    # FILE = "green_tripdata_2019-10.csv"
    # NAME = "green_taxi_data"
    main(table_name=NAME, file=FILE, db_url=URL, reset_table=True)
