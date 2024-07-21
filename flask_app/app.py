from flask import Flask, render_template
import psycopg2

# Database configuration New Change
db_user = 'postgres'
db_password = 'Vignesh07##'
db_host = 'localhost'
db_port = '5432'
db_name = 'tms'
schema_name = 'dt_stage'
table_name = 'tms_registrations'

app = Flask(__name__)

def connect_to_database():
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_name)
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

def fetch_data_from_db():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        query = f"SELECT * FROM {schema_name}.{table_name};"
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL:", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/')
def index():
    data = fetch_data_from_db()
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
