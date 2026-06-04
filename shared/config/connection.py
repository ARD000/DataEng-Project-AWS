import psycopg2
import os
import csv
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
host_name = os.environ.get("POSTGRES_HOST")
database_name = os.environ.get("POSTGRES_DB")
user_name = os.environ.get("POSTGRES_USER")
user_password = os.environ.get("POSTGRES_PASSWORD")

def create_database_tables():
    try:

        ### SETUP THE DATABASE CONNECTION
        print('Opening connection...')
        conn_string = f'host={host_name} dbname={database_name} user={user_name} password={user_password}'
        # Establish a database connection
        with psycopg2.connect(conn_string) as connection:

            print('Opening cursor...')
            cursor = connection.cursor()

    # ============================================
    #                CREATE TABLES

            print('Creating tables...')

            cursor.execute("DROP TABLE IF EXISTS orders;")
            create_table_sql =  """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                time TIME NOT NULL,
                location VARCHAR(50) NOT NULL,
                customer_name VARCHAR(30) NOT NULL,
                items_total TEXT NOT NULL,
                amount_paid DECIMAL(10, 2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                card_number VARCHAR(20) NOT NULL
            );
            """
            cursor.execute(create_table_sql)
            print('Orders table created successfully.')




    # ============================================
    #                FILL TABLES FROM CSV

            print('Filling tables from CSV file...')

           


    # ============================================
    #                 LOAD TO DATABASE

            print('\n\nCommiting. . .')
            connection.commit()

            print('Displaying all records. . .')
            cursor.execute("SELECT * FROM orders;")
            records = cursor.fetchall()
            for row in records:
                print(row)

                
            print('\nClosing cursor. . .')
            cursor.close()
            print('All done!')
            # The connection will automatically close here

    except Exception as ex:
        print('Failed to:', ex)


# =================================================

create_database_tables()
