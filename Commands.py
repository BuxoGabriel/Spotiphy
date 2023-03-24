import psycopg2
import datetime
def Help():
    print("""The Commands Available are as follows:
    help: gives this help command
    register: creates an account
    login: logs in to account
    account: displays account information
    collections: manipulation of collections
    quit: ends program""")

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
        curs.close()
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
           
                        
def Login(conn) -> tuple[int, str]:    
    curs = conn.cursor()                    
    username = input("Enter your username: ")
    password = input("Enter your password: ")
                        
    curs.execute("""SELECT uid, username FROM "User" WHERE username = %s AND password = %s""", 
                    (username, password))

    result = curs.fetchone()
    curs.close()
    if result == None:
        print("Login Failed: No User found matching credentials")
        return -1, ""
    print("Registered User Successfully!")
    print("Logged in as %s" % username)
    return result

def Collections(conn, uid):
    # Helper Func
    def gatherCollections(conn, uid):
        curs = conn.cursor()
        curs.execute("""SELECT c.name, c.cid FROM "UserCollection" uc, "Collection" c WHERE uc.uid = %s""",
            (uid,))
        # List of tuples(collection id, collection name)
        collection_list = curs.fetchall()
        amount_of_collections = len(collection_list)
        if amount_of_collections == 0:
            print("You have no collections")
        else:
            print("Your collections:")
            for i in range(amount_of_collections):
                print("%s: %s" % (i + 1, collection_list[i][0]))
        curs.close()
        return collection_list
    # Collections Start
    try:
        collection_list = gatherCollections(conn, uid)
        curs = conn.cursor()
        while True:
            print("""Available operations:
    create: create a new collection
    view: view a collection to add and delete songs
    sort: sort a collection by either song name, genre, year of release, or artist's name
    quit: leave collections""")
            command = input("Spotiphy Collections: ").lower().strip()
            match command:
                case "create" | "c":
                    # Gather Info
                    # Collection Name
                    collection_name = input("Collection Name: ")
                    while collection_name.strip() == "":
                        collection_name = input("Collection Name: ")
                    curs.execute("SELECT MAX(cid) FROM \"Collection\"")
                    # Collection ID
                    cid = curs.fetchone()[0] + 1
                    # Collection createDate
                    date_created = datetime.date.today()
                    curs.execute("""INSERT INTO "Collection"("cid", "name") VALUES (%s, %s)""", (cid, collection_name))
                    curs.execute("""INSERT INTO "UserCollection"("uid", "cid", "dateMade") VALUES (%s, %s, %s)""",
                        (uid, cid, date_created))
                    conn.commit()
                    print("Operation successful!")
                    collection_list = gatherCollections(conn, uid)

                case "view" | "v":
                    collection_number = int(input("Select Collection number: ")) - 1
                    collection_name, collection_id = collection_list[collection_number]
                    curs.execute("""SELECT s.title, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.cid = %s ORDER BY pos ASC""", (collection_id,))
                    tracklist = curs.fetchall()
                    amount_of_songs = len(tracklist)
                    print("Tracklist for Collection: %s" % collection_name)
                    for i in range(amount_of_songs):
                        song_title, song_id, trackNum = tracklist[i]
                        print("%s: %s" % (trackNum, song_title))

                case "sort" | "s":
                    category = input("Enter a category: ")
                    match category:
                        case "song name":
                            curs.execute("""SELECT s.title, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.cid = %s ORDER BY s.title""", (collection_id,))
                            tracklist = curs.fetchall()
                            amount_of_songs = len(tracklist)
                            print("Tracklist for Collection (in order by song name): %s" % collection_name)
                            for i in range(amount_of_songs):
                                song_title, song_id, trackNum = tracklist[i]
                                print("%s: %s" % (trackNum, song_title))
                        case "song genre":
                            curs.execute("""SELECT s.title, s.genre, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.cid = %s ORDER BY s.genre""", (collection_id,))
                            tracklist = curs.fetchall()
                            amount_of_songs = len(tracklist)
                            print("Tracklist for Collection (in order by song genre): %s" % collection_name)
                            for i in range(amount_of_songs):
                                song_title, song_genre, song_id, trackNum = tracklist[i]
                                print("%s: %s, %s" % (trackNum, song_title, song_genre))
                        case "year":
                            curs.execute("""SELECT s.title, s.year, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.cid = %s ORDER BY s.year""", (collection_id,))
                            tracklist = curs.fetchall()
                            amount_of_songs = len(tracklist)
                            print("Tracklist for Collection (in order by year): %s" % collection_name)
                            for i in range(amount_of_songs):
                                song_title, year, song_id, trackNum = tracklist[i]
                                print("%s: %s, %s" % (trackNum, song_title, year))
                        case "artist name":
                            curs.execute("""SELECT s.title, s.artist, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.cid = %s ORDER BY s.artist""", (collection_id,))
                            tracklist = curs.fetchall()
                            amount_of_songs = len(tracklist)
                            print("Tracklist for Collection (in order by artist name): %s" % collection_name)
                            for i in range(amount_of_songs):
                                song_title, artist, song_id, trackNum = tracklist[i]
                                print("%s: %s, %s" % (trackNum, song_title, artist))
            
                case "quit" | "q":
                    curs.close()
                    return

                case default:
                    print("Unrecognized Command!")
    except Exception as e:
        print("Operation Failed!")
        # print(e)