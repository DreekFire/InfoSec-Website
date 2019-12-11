import psycopg2
conn = None
try:
    conn = psycopg2.connect("dbname=postgres user=postgres")
    cur = conn.cursor()
    command = """INSERT INTO users (username, password)
             VALUES('DreekFire', 'communism') RETURNING user_id;"""
    cur.execute(command)
    cur.close()
    conn.commit()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed.')

        