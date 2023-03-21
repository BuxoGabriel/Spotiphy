import psycopg2
def Help():
    print("""The Commands Available are as follows:
-help: gives this help command
-quit: ends program
-register: creates an account
""")

def Register(conn):
    curs = conn.cursor()
    print("Registering a new user")
    username = input("Enter Your Username: ")
    curs.execute("""SELECT * FROM "User" WHERE username = %s""", (username,))
    if len(curs.fetchall()) != 0:
        print("Username Taken!")
        return
