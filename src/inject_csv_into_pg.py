"""Injecting local csv data into a postgres database."""

import pandas as pd
import sqlalchemy as sa
from pandas.io.parsers.readers import TextFileReader
from sqlalchemy import Engine, create_engine
from tqdm import tqdm

URL = "postgresql://root:root@localhost:5432/ny_taxi"
FILE = "yellow_tripdata_2021-01.csv"


def create_connection(url: str) -> Engine:
    """Sqlalchemy engine connecting to a db."""
    return create_engine(url)


def create_pd_iterator_from_csv(file: str, batch: int = 100000) -> TextFileReader:
    """Loads csv into a pd dataframe and creates iterator for batch injection."""
    df_iter = pd.read_csv(file, iterator=True, chunksize=batch)
    return df_iter


def init_table(columns: pd.DataFrame, conn: Engine) -> None:
    """Creates new table in postgres db. Drops existing table."""
    columns.to_sql(name="yellow_taxi_data", con=conn, if_exists="replace")


def convert_columns_to_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Converts dataframe columns to datetime."""
    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    return df


def main() -> None:
    """Injecting csv data into postgres db pipeline."""
    df_iter = create_pd_iterator_from_csv(FILE)
    conn = create_connection(URL)
    df = next(df_iter)

    if not sa.inspect(conn).has_table("yellow_taxi_data"):
        init_table(df.head(n=0), conn)

    for batch in tqdm(df_iter):
        batch = convert_columns_to_datetime(batch)
        batch.to_sql(name="yellow_taxi_data", con=conn, if_exists="append")


if __name__ == "__main__":
    main()
