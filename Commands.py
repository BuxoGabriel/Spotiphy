import psycopg2
import hashlib
import random
import datetime
import Helpers as h

def Help():
    print("""\nThe Commands Available are:
    help: gives this help command
    register: creates an account
    login: logs in to account
    account: displays account information
    friends: add, remove, and view friends
    collections: manipulate and listen to your collections
    search: lets you search for a song or album to add to collection or listen
    recommend: enjoy custom currated collections for you
    genre: discover the most popular genres through a given month
    quit: ends program""")

### Register Command
# Registers User
# Returns uid and username in a tuple
# Returns -1, "" if operation fails
def Register(conn) -> tuple[int, str]:
    print("\nRegistering new user")
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
        passlength = len(password)
    # TODO if time make alternate chars
    password += username
    password = hashlib.sha3_512(password.encode()).hexdigest()

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
    print("\nLogging in user")
    curs = conn.cursor()   
        
    username = input("Enter your username: ")
    # TODO if salt method changes in register change here as well
    password = input("Enter your password: ") + username
    # Hash Password
    password = hashlib.sha3_512(password.encode()).hexdigest()
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
def Friends(conn, uid):
    while True:
        friends = h.FetchFollowing(conn, uid)
        friend_count = len(friends)
        print("Friends list:")
        for i in range(friend_count):
            fid, username = friends[i]
            print("%s: %s" % (i + 1, username))
        print("""\nAvailable operations: 
    add: add a new friend
    remove: remove a friend from your friend list
    quit: leave friends""")
        command = input("Spotiphy Friends: ").lower().strip()
        match command:
            case "add" | "a":
                email = input("Friend's Email: ")
                curs = conn.cursor()
                curs.execute("""SELECT uid FROM "User" WHERE email = %s""", (email,))
                fid = curs.fetchone()
                if fid == None:
                    print("User with this email not found!")
                    continue
                fid = fid[0]
                curs.execute("""INSERT INTO "Friends"(uid1, uid2) VALUES(%s, %s)""", (uid, fid))
                conn.commit()
                curs.close()
                print("Added Friend Successfully!")
            case "remove" | "r":
                friend_index = int(input("Select Friend Number: ")) - 1
                if(friend_index >= len(friends)):
                    print("Friend %s does not exist" % friend_index)
                fid, username = friends[friend_index]
                curs = conn.cursor()
                curs.execute("""DELETE FROM "Friends" WHERE uid1 = %s AND uid2 = %s""", (uid, fid))
                conn.commit()
                curs.close()
            case "quit" | "q":
                return

### Collections Command
def Collections(conn, uid):
    try:
        collection_list = h.FetchCollections(conn, uid)
        while True:
            # Print Collections
            print("\nCollections:")
            for i in range(len(collection_list)):
                print("%s. %s" % (i + 1, collection_list[i][0]))
            
            # Print available commands
            print("""\nAvailable operations:
    create: create a new collection
    delete: delete a collection
    view: view a collection to add and delete songs
    number: find how many collections you have
    listen: listen to all the songs in collection

    quit: leave collections""")
            command = input("Spotiphy Collections: ").lower()
            match command:
                case "create" | "c":
                    h.CreateCollection(conn, uid)
                    collection_list = h.FetchCollections(conn, uid)
                case "delete" | "d":
                    h.DeleteCollection(conn, collection_list)
                    collection_list = h.FetchCollections(conn, uid)
                case "view" | "v":
                    h.ViewCollection(conn, collection_list)
                case "listen" | "l":
                    h.Listen(conn, uid, collection_list)
                case "number" | "n":
                    print("The number of collections you have right now is " + str(h.findNumberofCollections(conn, uid)) + ".")
                case "quit" | "q":
                    return
                case default:
                    print("Unrecognized Command!")
    except Exception as e:
        print("Operation Failed!")
        print(e)

### Search Command
def Search(conn, loggedIn, uid):
    category = input("\nWhat would you like to search for(song, album): ")
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

            while True:
                # Print Songs
                song_amount = len(results)
                print("\nFound Songs:")
                for i in range(song_amount):
                    artist, title, album, sid, song_length = results[i]
                    print(
                        (((((str(i + 1) + ": ").ljust(10, " ")
                        + " Artist: " + artist).ljust(50, " ") 
                        + " Title: " + title).ljust(75, " ")
                        + " Album: " + album).ljust(100, " ")
                        + " Song length: " + str(song_length)).ljust(150, " ")
                    )
                print("""\nAvailable operations:
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
                        
                        # Show Collections
                        user_collections = h.FetchCollections(conn, uid)
                        for i in range(len(user_collections)):
                            print("%s. %s" % (i + 1, user_collections[i][0]))

                        # Get cid
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
        
def Account(conn, uid, username):
    print("\nLogged in as %s" % username)
    print("User ID: %s" % uid)
    while True:
        print("""\nAvailable operations:
        followers: check how many people you follow and how many followers you have
        collections: check how many collections you have
        top: show the top 10 artists that the user listens to
        quit: leave account profile""")
        command = input("Spotiphy Account Profile: ")
        match command:
            case "followers" | "f":
                numFollowing = h.FetchFollowing(conn, uid, count=True)[0][0]
                numFollowers = h.FetchFollowers(conn, uid, count=True)[0][0]
                print("Following:  %s" % numFollowing)
                print("Followers: %s" % numFollowers)
            case "collections" | "c":    
                numCollections = h.FetchCollections(conn, uid, count=True)[0][0]
                print("Collections: %s" % numCollections)
            case "top" | "t":
                print("""\nAvailable operations:
                plays: show top 10 artists by most plays 
                collections: show top 10 artists by additions to collections
                both: show top 10 artists by a combination of most plays and collections
                quit: leave top 10 artists command line""")
                curs = conn.cursor()
                t10c = input("Spotiphy Top 10 Artists: ")
                match t10c:
                    case  "plays" | "p":
                        curs.execute("""SELECT name, COUNT(*) from (SELECT ars.uid, ars.sid, ars.arid, "Artist".name from (SELECT s.uid, s.sid, "SongArtist".arid  from (SELECT "User".uid, "ListenHistory".sid from "User"
                                        INNER JOIN "ListenHistory" ON "User".uid = "ListenHistory".uid
                                        ORDER BY uid) as s
                                        INNER JOIN "SongArtist" ON s.sid = "SongArtist".sid) as ars
                                        INNER JOIN "Artist" ON ars.arid = "Artist".arid
                                        ORDER BY arid) as a
                                        WHERE a.uid = %s
                                        GROUP BY name
                                        ORDER BY count(*) DESC
                                        LIMIT 10""", (uid,))
                        c = curs.fetchall()
                        print("Your top 10 most played artists are:")
                        for a in range(len(c)):
                            print(str(a+1) + ". " + c[a][0])
                            
                    case  "collections" | "c":
                        curs.execute("""SELECT name, COUNT(*) from (SELECT ucs.uid, a.name from (
                        SELECT uu.uid, uu.cid, ct.sid from (SELECT u.uid, uc.cid from "User" as u
                        INNER JOIN "UserCollection" uc on u.uid = uc.uid) as uu
                        INNER JOIN "CollectionTrackList" ct ON uu.cid = ct.cid) as ucs
                        INNER JOIN "SongArtist" sa ON sa.sid = ucs.sid
                        INNER JOIN "Artist" a ON sa.arid = a.arid) as f
                        WHERE f.uid = %s
                        GROUP BY name
                        ORDER BY count(*) DESC
                        LIMIT 10""", (uid,))
                        c = curs.fetchall()
                        print("Your top 10 most played artists (from your collections) are:")
                        for a in range(len(c)):
                            print(str(a+1) + ". " + c[a][0])
                            
                    case  "both" | "b":
                        curs.execute("""SELECT name, COUNT(*) from
                        (SELECT u.uid, a.name from "User" as u
                        INNER JOIN "UserCollection" uc on u.uid = uc.uid
                        INNER JOIN "CollectionTrackList" ct ON uc.cid = ct.cid
                        INNER JOIN "ListenHistory" lh ON u.uid = lh.uid
                        INNER JOIN "SongArtist" sa ON sa.sid = ct.sid
                        INNER JOIN "Artist" a ON sa.arid = a.arid) as f
                        WHERE f.uid = '200'
                        GROUP BY name
                        ORDER BY count(*) DESC
                        LIMIT 10""", (uid,))
                        c = curs.fetchall()
                        print("Your top 10 most played artists (from your collections) are:")
                        for a in range(len(c)):
                            print(str(a+1) + ". " + c[a][0])
                            
                    case "quit" | "q":
                        break
        
            case "quit" | "q":
                break

def Recommend(conn, uid):
    while(True):
        print("""\nWe have currated a list of collections for you to listen to.
In order to view a collection simply select one from the following list by its number(or type q to quit):
1. Friends' Recent Listens""")
        command = input("\nSpotiphy Recommendations: ").lower()
        match command:
            case "1":
                collection = h.FetchTop50(conn, uid)
            case "q":
                break
            case default:
                continue
        collection_length = len(collection)
        for i in range(collection_length):
            print("%s. %s" % (i + 1, collection[i][0]))
        print("""\nAvailable operations: 
listen: listen to this collection
add: add this to my collections
ignore: go back to Spotiphy Recommendations""")
        command = input("\nSpotiphy Collection View: ").lower()
        match command:
            case "add":
                cid = h.CreateCollection(conn, uid)
                curs = conn.cursor()
                for i in range(collection_length):
                    curs.execute("""INSERT INTO "CollectionTrackList"("cid", "sid", "posNum") VALUES (%s, %s, %s) """,
                        (cid, collection[i][1], i + 1))
                conn.commit()
                curs.close()
                print("Added all songs to collection successfully!\n Operation Complete!")
            case "listen":
                h.ListenTracklist(conn, uid, collection)
            
            case default: 
                pass
            
### (Popular) Genre Command
def popularGenre(conn, uid):
    while True:
        inp = input("Enter a number corresponding to a month: ")
        month = int(inp)
        if month > 12 or month < 1:
            print("Invalid month. Please enter a number between (and including) 1 and 12")
        else:
            curs = conn.cursor()
            curs.execute("""SELECT name, COUNT(*) from (SELECT date_part('month', "releaseDate"), g.name FROM "Album" as a
                            INNER JOIN "AlbumGenre" ag on ag.aid = a.aid
                            INNER JOIN "Genre" g on g.gid = ag.gid
                            WHERE date_part('month', "releaseDate") = %s) as d

                            GROUP BY name
                            ORDER BY COUNT(*) DESC
                            LIMIT 5
                            """, (inp,))
            c = curs.fetchall()
            print("The top 5 most popular genres of month " + inp + " are:")
            for a in range(len(c)):
                print(str(a+1) + ". " + c[a][0])
            break
                            
        
