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
            global_uid = -1
            global_username = ""

            Commands.Help()
            while True:
                command = input("Spotiphy: ").lower()
                if command == "":
                    continue

                match command:
                    case "quit" | "q":
                        break
                    case "help" | "h":
                        Commands.Help()
                    case "register" | "r":
                        uid, username = Commands.Register(conn)
                        if uid != -1:
                            loggedIn = True
                            global_uid = uid
                            global_username = username
                    case "login" | "l":
                        uid, username = Commands.Login(conn)
                        if uid != -1:
                            loggedIn = True
                            global_uid = uid
                            global_username = username
                    case "account" | "a":
                        if not loggedIn: print("Not logged in")
                        else:
                            print("Logged in as %s" % global_username)
                            print("User ID: %s" % global_uid)
                    case "collections" | "c":
                        if not loggedIn: 
                            print("You are not logged in")
                            print("You must be logged in in order to alter collections")
                        else:
                            Commands.Collections(conn, global_uid)
                    case "search" | "s":
                        Commands.Search(conn, loggedIn, global_uid)
                    case default:
                        print("Unrecognized command!")
    except Exception as e:
        print(e)
    finally:
        conn.close()
        print("Connection Closed. Goodbye!")

if __name__ == "__main__":
    main()