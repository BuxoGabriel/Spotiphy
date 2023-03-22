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

            print("Welcome to Spotiphy!\nConnecting to database...")
            conn = psycopg2.connect(**params)
            print("Database connection established!")
            
            loggedIn = False
            uid = -1
            username = ""

            Commands.Help()
            while True:
                userInp = input("Spotiphy: ").lower().split()
                args = len(userInp)
                if args == 0:
                    continue
                command = userInp[0]

                match command:
                    case "quit":
                        break
                    case "help":
                        Commands.Help()
                    case "register":
                        uid, username = Commands.Register(conn)
                        if uid != -1:
                            loggedIn = True
    except Exception as e:
        print(e)
    finally:
        conn.close()
        print("Connection Closed. Goodbye!")

if __name__ == "__main__":
    main()