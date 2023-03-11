import psycopg2
from sshtunnel import SSHTunnelForwarder

def loadConfig():
    with open(".env", "r") as f:
        return f.readline().strip(), f.readline().strip()

def main():
    DBNAME = "p320_20"
    USERNAME, PASSWORD = loadConfig()
    try:
        with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                                ssh_username=USERNAME,
                                ssh_password=PASSWORD,
                                remote_bind_address=('localhost', 5432)) as server:
            server.start()
            print("SSH tunnel established")
            params = {
                'database': DBNAME,
                'user': USERNAME,
                'password': PASSWORD,
                'host': 'localhost',
                'port': server.local_bind_port
            }

            conn = psycopg2.connect(**params)
            curs = conn.cursor()
            print("Database connection established")
            print(curs.fetchall())
            conn.close()
    except Exception as e:
        print("Connection failed")
        print(e)

if __name__ == "__main__":
    main()