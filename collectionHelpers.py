import datetime
# Helper Functions

def GatherCollections(conn, uid):
    curs = conn.cursor()
    curs.execute("""SELECT c.name, c.cid FROM "UserCollection" uc, "Collection" c WHERE uc.cid = c.cid AND uc.uid = %s """,
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

def ViewCollection(conn, uid, collection_list):
    curs = conn.cursor()

    collection_number = int(input("Select Collection number: ")) - 1
    # error checking collection number value
    if collection_number not in range(len(collection_list)):
        print("" + collection_number + "is not a valid collection!")
        curs.close()
        return
    
    collection_name, collection_id = collection_list[collection_number]
    curs.execute("""SELECT s.title, s.sid, tl."posNum" as pos FROM "Song" s, "CollectionTrackList" tl WHERE tl.sid = s.sid AND tl.cid = %s ORDER BY pos ASC""",
                    (collection_id,))
    tracklist = curs.fetchall()
    amount_of_songs = len(tracklist)
    print("Tracklist for Collection: %s" % collection_name)
    for i in range(amount_of_songs):
        song_title, song_id, trackNum = tracklist[i]
        print("%s: %s" % (trackNum, song_title))
    return tracklist
