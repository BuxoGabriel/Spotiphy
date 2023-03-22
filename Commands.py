import psycopg2
import datetime
def Help():
    print("""The Commands Available are as follows:
- help: gives this help command
- quit: ends program
- register: creates an account
""")

# Registers User
# Returns uid and username in a tuple
# Returns -1, "" if operation fails
def Register(conn) -> tuple[int, str]:
    print("Registering new user")
    curs = conn.cursor()

    # Gather User Info Input
    # Username
    username = input("Enter your Username: ")
    while username.strip() == "":
        username = input("Enter your Username: ")
    # Check if username taken
    curs.execute("""SELECT * FROM "User" WHERE username = %s""", (username,))
    if len(curs.fetchall()) != 0:
        print("Register User Failed: Username Taken!")
        return -1, ""
    # Password
    password = input("Enter a password between 6 and 16 characters: ")
    passlength = len(password)
    while passlength < 6 or passlength > 16 or password.strip() == "":
        password = input("Enter a password between 6 and 16 characters: ")
    # First Name
    firstName = input("Enter your first name: ")
    while firstName.strip() == "":
        firstName = input("Enter your first name: ")
    # Last Name
    lastName = input("Enter your last name: ")
    while lastName.strip() == "":
        lastName = input("Enter your last name: ")
    # Email
    email = input("Enter your email: ")
    while email.strip() == "":
        email = input("Enter your email: ")

    # Create uid and joinDate
    curs.execute("SELECT MAX(uid) FROM \"User\"")
    uid = curs.fetchone()[0] + 1
    joinedDate = datetime.date.today()

    # Add user to Database
    curs.execute("""INSERT INTO "User"("uid", "username", "password", "firstName", "lastName", "email", "joinedDate") VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (uid, username, password, firstName, lastName, email, joinedDate))
    conn.commit()
    curs.close()

    print("Registered User Successfully!")
    print("Logged in as %s!" % username)
    return uid, username