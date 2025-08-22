
import os
import hashlib
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, String, text, Integer, Float, DateTime
from sqlalchemy.orm import sessionmaker
load_dotenv()

class RDSPostgresDB:
    def __init__(self):
        # Load from .env
        db_host = os.getenv("AWS_DB_HOST")
        db_port = os.getenv("AWS_DB_PORT")
        db_name = os.getenv("AWS_DB_NAME")
        db_user = os.getenv("AWS_DB_USER")
        db_pass = os.getenv("AWS_DB_PASS")

        # PostgreSQL connection string
        conn_str = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        self.engine = create_engine(conn_str, echo=False)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.create_database()

    def create_database(self):
        """Creates the database if it does not exist."""
        try:
            self.engine.connect()
            print("Database connection established.")
        except Exception as e:
            print(f"Error connecting to the database: {e}")

    def create_table(self, table_name, columns_with_types):
        """Creates a table dynamically with a SHA-256 hash primary key to prevent duplicates."""
        table = Table(
            table_name, self.metadata,
            Column("id", String, primary_key=True),  # Primary key hash column
            *[Column(col, col_type) for col, col_type in columns_with_types],
        )
        try:
            table.create(self.engine, checkfirst=True)
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

    def delete_table(self, table_name):
        """Deletes a table if it exists."""
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            table.drop(self.engine)
            print(f"Table {table_name} deleted.")
        except Exception as e:
            print(f"Error deleting table {table_name}: {e}")

    def generate_hash(self, data):
        """Generates a SHA-256 hash over the string representation of a row."""
        row_string = str(sorted(data.items()))  # Ensure consistent ordering
        return hashlib.sha256(row_string.encode()).hexdigest()

    def insert_data(self, table_name, data):
        """Inserts a row into the table using parameterized queries and avoids duplicates."""
        data["id"] = self.generate_hash(data)
        placeholders = ", ".join([f":{key}" for key in data.keys()])
        query = text(f"""
            INSERT INTO {table_name} ({', '.join(data.keys())})
            VALUES ({placeholders})
            ON CONFLICT(id) DO NOTHING
        """)
        self.session.execute(query, data)
        self.session.commit()

    def query_data(self, query, max_retries=2):
        """Executes a SELECT query and returns results with column names."""
        for attempt in range(max_retries):
            try:
                result = self.session.execute(text(query))
                columns = result.keys()
                data = [list(row) for row in result.fetchall()]
                return list(columns), data
            except Exception as e:
                print(f"Query attempt {attempt + 1} failed: {e}")
                
                # Check if it's a transaction error
                if "InFailedSqlTransaction" in str(e) or "aborted" in str(e).lower():
                    print("Transaction error detected. Rolling back and reconnecting...")
                    self.rollback_transaction()
                    self.close_and_reconnect()
                
                # If this is the last attempt, raise the exception
                if attempt == max_retries - 1:
                    print(f"All {max_retries} attempts failed.")
                    raise e
                
                print(f"Retrying in attempt {attempt + 2}...")
        
        # This should never be reached, but just in case
        raise Exception("Unexpected error in query_data retry logic")
    
    def rollback_transaction(self):
        """Rolls back the current transaction."""
        try:
            self.session.rollback()
            print("Transaction rolled back successfully.")
        except Exception as e:
            print(f"Error rolling back transaction: {e}")

    def close_and_reconnect(self):
        """Closes the current session and reconnects to the database."""
        try:
            self.session.close()
            self.session = self.Session()
            print("Reconnected to the database successfully.")
        except Exception as e:
            print(f"Error reconnecting to the database: {e}")

    def __del__(self):
        self.session.close()


RDS_POSTGRES_DB = RDSPostgresDB()