def Help():
    print("""The Commands Available are as follows:
    help: gives this help command
    quit: ends program""")

                        
                        
def Login():                        
    username = input("Please enter your username: ")
    password = input("Please enter your password: ")
                        
    cur.execute("""
    SELECT username, password FROM User
    WHERE username == "%s" AND password == "%s" """, (username, password))

    if cur.fetchone() == None:
        print("Invalid")
