import datetime
# Helper Functions

# !count Returns tuple[col name, col id]
# count Returns [(count)] count = result[0][0]
def FetchCollections(conn, uid, count = False) -> list[tuple[str, int]]:
    if count:
        SQL = """SELECT COUNT(*) FROM "UserCollection" WHERE uid = %s"""
    else:
        SQL = """SELECT c.name, c.cid FROM "UserCollection" uc, "Collection" c WHERE uc.cid = c.cid AND uc.uid = %s """
    curs = conn.cursor()
    curs.execute(SQL, (uid,))
    # List of tuples(collection id, collection name)
    result = curs.fetchall()
    curs.close()
    return result

def CreateCollection(conn, uid):
    curs = conn.cursor()
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
    curs.close()
    print("Operation successful!")
    return cid

def DeleteCollection(conn, collection_list: list[tuple[str, int]]): 
    collection_number = int(input("Select Collection number: ")) - 1
    # error checking collection number value
    if collection_number not in range(len(collection_list)):
        print("" + collection_number + "is not a valid collection!")
        return
    curs = conn.cursor()
    collection = collection_list[collection_number]
    cid = collection[1]
    curs.execute("""DELETE FROM  "CollectionTrackList" WHERE cid = %s""", (cid,))
    conn.commit()
    curs.execute("""DELETE FROM  "UserCollection" WHERE cid = %s""", (cid,))
    conn.commit()
    curs.execute("""DELETE FROM "Collection" WHERE cid = %s""", (cid,))
    conn.commit()
    curs.close()
    print("Deleted Collection successfully!")
    return

# Returns array of tuples(title, sid, posNum, songlength)
def FetchTracklist(conn, collection_list: list[tuple[str, int]]) -> list[tuple[str, int, int, int]]:
    curs = conn.cursor()

    collection_number = int(input("Select Collection number: ")) - 1
    # error checking collection number value
    if collection_number not in range(len(collection_list)):
        print("" + collection_number + "is not a valid collection!")
        curs.close()
        return
    
    collection = collection_list[collection_number]
    curs.execute("""SELECT s.title, s.sid, tl."posNum", s.songlength as pos FROM "Song" s, "CollectionTrackList" tl
        WHERE tl.sid = s.sid AND tl.cid = %s
        ORDER BY pos ASC""",
                    (collection[1],))
    tracklist = curs.fetchall()
    curs.close()
    return tracklist, collection

def ViewCollection(conn, collection_list: list[tuple[str, int]]):
    tracklist, collection = FetchTracklist(conn, collection_list)
    amount_of_songs = len(tracklist)
    print("Tracklist for Collection: %s" % collection[0]) #col[0] is col name
    for i in range(amount_of_songs):
        song_title, sid, trackNum, song_length = tracklist[i]
        print("%s: %s" % (trackNum, song_title))
    return

def Listen(conn, uid, collection_list):
    tracklist, collection = FetchTracklist(conn, collection_list)
    amount_of_songs = len(tracklist)
    print("You are listening to %s" % collection[0])
    curs = conn.cursor()
    time_elapsed = 0
    for i in range(amount_of_songs):
        song_title, sid, trackNum, song_length  = tracklist[i]
        print("listening to %s..." % song_title)
        date_listened = datetime.datetime.now()
        curs.execute("""INSERT INTO "ListenHistory"("uid", "sid", "date") VALUES (%s, %s, %s)""", (uid, sid, date_listened))
        time_elapsed += song_length
    print("Finished listening to %s. Total Time Elapsed: %s" % (collection[0], time_elapsed))
    conn.commit()
    curs.close()

# !count Returns tuple[friend id, friend name]
# count Returns [(count)] count = result[0][0]
def FetchFollowing(conn, uid, count = False) -> list[tuple[int, str]]:
    if count:
        SQL = """SELECT COUNT(*) FROM "Friends" WHERE uid1 = %s"""
    else:
        SQL = """SELECT f.uid2, u.username FROM"Friends" f, "User" u WHERE u.uid = f.uid2 AND uid1 = %s"""
    curs = conn.cursor()
    curs.execute(SQL, (uid,))
    result = curs.fetchall()
    curs.close()
    return result

# !count Returns tuple[friend id, friend name]
# count Returns [(count)] count = result[0][0]
def FetchFollowers(conn, uid, count = False) -> list[tuple[int, str]]:
    if count:
        SQL = """SELECT COUNT(*) FROM "Friends" WHERE uid2 = %s"""
    else:
        SQL = """SELECT f.uid1, u.username FROM "Friends" f, "User" u WHERE u.uid = f.uid1 AND uid2 = %s"""
    curs = conn.cursor()
    curs.execute(SQL, (uid,))
    result = curs.fetchall()
    curs.close()
    return result
    
def findNumberofCollections(conn, uid):
    curs = conn.cursor()
    curs.execute("""SELECT c.name, c.cid FROM "UserCollection" uc, "Collection" c WHERE uc.cid = c.cid AND uc.uid = %s """,
        (uid,))
    # List of tuples(collection id, collection name)
    collection_list = curs.fetchall()
    amount_of_collections = len(collection_list)
    return amount_of_collections

# Gets the 50 most listened to songs amoung friends in the past 30 days
def FetchTop50(conn, uid):
    SQL = """
    SELECT title, sid, songlength FROM "Song" WHERE sid in(
    SELECT lh.sid FROM "Friends" f, "ListenHistory" lh 
        WHERE f.uid1 = %s AND lh.date >= NOW() - INTERVAL '30 days'
        GROUP BY lh.sid
        ORDER BY COUNT(lh.sid) DESC
        LIMIT 50) """
    curs = conn.cursor()
    curs.execute(SQL, (uid,))
    result = curs.fetchall()
    return result

def ListenTracklist(conn, uid, collection: list[tuple[str, int, int]]):
    curs = conn.cursor()
    time_elapsed = 0
    date = datetime.datetime.now()
    for title, sid, songlen in collection:
        print("listening to %s..." % title)
        time_elapsed += songlen
        if(uid != -1):
            curs.execute("""INSERT INTO "ListenHistory"(uid, sid, date) VALUES (%s, %s, %s) """ % (uid, sid, date))
    print("Finished listening! Total Time Elapsed: %s" % (collection[0], time_elapsed))
    
