import psycopg2
import hashlib
import random
import datetime
import Helpers as h

HASHER = hashlib.sha3_256()

def Help():
    print("""The Commands Available are:
    help: gives this help command
    register: creates an account
    login: logs in to account
    account: displays account information
    friends: add, remove, and view friends
    collections: manipulate and listen to your collections
    search: lets you search for a song or album to add to collection or listen
    quit: ends program""")

### Register Command
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
    # TODO if time make alternate chars
    saltedPass = password + username
    HASHER.update(saltedPass.encode('utf-8'))
    # Hashed password
    password = HASHER.hexdigest()

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
           
### Login Command
# Returns uid and username of user
# returns -1 "" if it cant find user in databasea            
def Login(conn) -> tuple[int, str]:    
    curs = conn.cursor()       
    username = input("Enter your username: ")
    # TODO if salt method changes in register change here as well
    password = input("Enter your password: ") + username
    # Hash Password
    HASHER.update(password.encode('utf-8'))
    password = HASHER.hexdigest()
                        
    curs.execute("""SELECT uid, username FROM "User" WHERE username = %s AND password = %s""", 
                    (username, password))

    result = curs.fetchone()
    curs.close()
    if result == None:
        print("Login Failed: No User found matching credentials")
        return -1, ""
    print("Logged in as %s" % username)
    return result

### Friends Command
# Helper Function
def FetchFriends(conn, uid):
    curs = conn.cursor()
    curs.execute("""SELECT f.uid2, u.username from "Friends" f, "User" u WHERE f.uid2 = u.uid AND uid1 = %s """, (uid,))
    result = curs.fetchall()
    curs.close()
    return result
    

def Friends(conn, uid):
    while True:
        friends = FetchFriends(conn, uid)
        friend_count = len(friends)
        print("Friends list:")
        for i in range(friend_count):
            fid, username = friends[i]
            print("%s: %s" % (i + 1, username))
        print("""Available operations: 
    add: add a new friend
    remove: remove a friend from your friend list
    quit: leave friends""")
        command = input("Spotiphy Friends: ").lower().strip()
        match command:
            case "add" | "a":
                email = input("Friend's Email: ")
                curs = conn.cursor()
                curs.execute("""SELECT uid FROM "User" WHERE email = %s""", (email,))
                fid = curs.fetchone()[0]
                curs.execute("""INSERT INTO "Friends"(uid1, uid2) VALUES(%s, %s)""", (uid, fid))
                conn.commit()
                curs.close()
                print("Added Friend Successfully!")
            case "remove" | "r":
                friend_index = int(input("Select Friend Number: ")) - 1
                fid, username = friends[friend_index]
                curs = conn.cursor()
                curs.execute("""DELETE FROM "Friends" WHERE uid1 = %s AND uid2 = %s""", (uid, fid))
                conn.commit()
                curs.close()
            case "quit" | "q":
                print()
                return
### Collections Command

def Collections(conn, uid):
    try:
        collection_list = h.GatherCollections(conn, uid)
        while True:
            print("""Available operations:
    create: create a new collection
    delete: delete a collection
    view: view a collection to add and delete songs
    listen: listen to all the songs in collection
    quit: leave collections""")
            command = input("Spotiphy Collections: ").lower().strip()
            match command:
                case "create" | "c":
                    h.CreateCollection(conn, uid)
                    collection_list = h.GatherCollections(conn, uid)
                case "delete" | "d":
                    h.DeleteCollection(conn, collection_list)
                case "view" | "v":
                    h.ViewCollection(conn, collection_list)
                case "listen" | "l":
                    h.Listen(conn, uid, collection_list)
                case "quit" | "q":
                    return
                case default:
                    print("Unrecognized Command!")
    except Exception as e:
        print("Operation Failed!")
        print(e)

### Search Command
def Search(conn, loggedIn, uid):
    category = input("What would you like to search for(song, album): ")
    match category:
        case "song":
            search_type = input("Search by(name, artist, album, and genre) or type quit: ")
            curs = conn.cursor()
            match search_type:
                case "name":
                    inp = "%" + input("Song Title: ") + "%"
                    curs.execute("""SELECT ar.name, s.title, al.name, s.sid, s.songlength 
                    FROM "Song" s, "Album" al, "AlbumTrackList" atl,"SongArtist" sa, "Artist" ar 
                    WHERE s.sid = sa.sid AND sa.arid = ar.arid AND s.sid = atl.sid AND atl.aid = al.aid 
                        AND s.title LIKE %s
                    ORDER BY al.name, atl."trackNo" """, (inp,))
                case "artist":
                    inp = "%" + input("Artist Name: ") + "%"
                    curs.execute("""SELECT ar.name, s.title, al.name, s.sid, s.songlength 
                    FROM "Song" s, "Album" al, "AlbumTrackList" atl,"SongArtist" sa, "Artist" ar 
                    WHERE s.sid = sa.sid AND sa.arid = ar.arid AND s.sid = atl.sid AND atl.aid = al.aid 
                        AND ar.name LIKE %s
                    ORDER BY al.name, atl."trackNo" """, (inp,))
                case "album":
                    inp = "%" + input("Album Name: ") + "%"
                    curs.execute("""SELECT ar.name, s.title, al.name, s.sid, s.songlength 
                    FROM "Song" s, "Album" al, "AlbumTrackList" atl,"SongArtist" sa, "Artist" ar 
                    WHERE s.sid = sa.sid AND sa.arid = ar.arid AND s.sid = atl.sid AND atl.aid = al.aid 
                        AND al.name LIKE %s
                    ORDER BY al.name, atl."trackNo" """, (inp,))
                case "genre":
                    pass
                case "quit":
                    curs.close()
                    return
                case default:
                    print("Command " + search_type + "does not exist!")
                    curs.close()
                    return
            results = curs.fetchall()
            song_amount = len(results)
            for i in range(song_amount):
                artist, title, album, sid, song_length = results[i]
                print(
                    (((((str(i + 1) + ": ").ljust(10, " ")
                      + " Artist: " + artist).ljust(50, " ") 
                      + " Title: " + title).ljust(75, " ")
                     + " Album: " + album).ljust(100, " ")
                     + " Song length: " + str(song_length)).ljust(150, " ")
                )
            while True:
                print("""Available operations:
    add: adds a song to one of your collections
    listen: listen to a song
    quit: leave search song""")
                command = input("Spotiphy Search Song: ")
                match command:
                    case "add":
                        if not loggedIn:
                            print("Can not add song. Not logged in!")
                            return
                        # Get sid
                        song_selected = int(input("Select a song: ")) - 1
                        sid = results[song_selected][3]
                        # Get cid
                        user_collections = h.GatherCollections(conn, uid)
                        collection_number = int(input("Select Collection number: ")) - 1
                        cid = user_collections[collection_number][1]
                        # Get posNum
                        curs.execute("""SELECT MAX("posNum") FROM "CollectionTrackList" WHERE cid = %s """, (cid,))
                        posNum = curs.fetchone()[0]
                        if posNum is None:
                            posNum = 1
                        else:
                            posNum += 1
                        # Insert to Collection
                        # TODO Check if the song has already been added to the playlist
                        curs.execute("""INSERT INTO "CollectionTrackList"("cid", "sid", "posNum") VALUES (%s, %s, %s) """, (cid, sid, posNum))
                        conn.commit()
                        curs.close()
                        print("Song added to collection!")
                    case "listen" | "l":
                        # Get sid
                        song_selected = int(input("Select a song: ")) - 1
                        artist_name, song_title, album_name, sid, songlength  = results[song_selected]
                        print("listening to: %s..." % song_title)
                        if loggedIn:
                            date_listened = datetime.datetime.now()
                            curs.execute("""INSERT INTO "ListenHistory"("uid", "sid", "date") VALUES (%s, %s, %s)""", (uid, sid, date_listened))
                            conn.commit()
                        print("Finished listening to %s. Time Elapsed: %ss" % (song_title, songlength))
                    case "quit" | "q":
                        curs.close()
                        break
        case "album":
           # TODO
           pass 