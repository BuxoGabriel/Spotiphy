import psycopg2
from sshtunnel import SSHTunnelForwarder
import Commands

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

            print("Welcome to Spotiphy! Connecting to database...")
            conn = psycopg2.connect(**params)
            curs = conn.cursor()
            print("Database connection established")
            
            Commands.Help()
            while True:
                userInp = input().lower().split()
                args = len(userInp)
                command = userInp[0]
                if args == 0:
                    continue

                match command:
                    case "quit":
                        break
                    case "help":
                        Commands.Help()
                    case "login":
                        Commands.Login()


    except Exception as e:
        print("Connection failed")
        print(e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()