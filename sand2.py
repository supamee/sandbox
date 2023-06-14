
import sqlite3

def open_db(nam):
    conn = sqlite3.connect(nam)
    conn.row_factory = sqlite3.Row
    # print ("Openned database %s as %r" % (nam, conn))
    return conn

class WifiRecord():
    def __init__(
        self,
        wifi_id: str,
        address: str = None,
        sentry: str = None,
        start_timestamp: float = None,
        end_timestamp: float = None,
        antenna: list = list(),
        attr: dict = dict(),
        **kwargs,
    ):
        self.wifi_id = wifi_id
        self.address = address
        self.sentry = sentry
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.antenna = antenna
        self.attr = attr


def row_to_wifi(rows):
    wifis = []
    if not isinstance(rows, list):
        rows = [rows]
    for row in rows:
        if row is not None and len(row) == 9:
            wifi = WifiRecord(row[0])
            wifi.address = row[1]
            wifi.sentry = row[2]
            wifi.start_timestamp = row[3]
            wifi.end_timestamp = row[4]
            wifi.antenna = [row[5], row[6]]
            wifi.attr = json.loads(row[7])
            wifis.append(wifi)
       
    return wifis
# SELECT * FROM table ORDER BY timestamp DESC LIMIT 1
# ASC
# DESC
gaps=[]
path="shepherd_tool/nvme/strive/wifi.db"
conn = open_db(path)
cursor = conn.cursor() 
cursor.execute(
        f"""
        SELECT start_timestamp, end_timestamp 
        FROM wifis
        WHERE end_timestamp IS NOT NULL AND end_timestamp != 'NULL'
        ORDER BY end_timestamp DESC LIMIT 1
        """
    )
row = cursor.fetchone()
print("\nfirst",row[0],row[1])
while row:
    start=row[0]
    while row:
        cursor = conn.cursor() 
        cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE (end_timestamp IS NULL OR end_timestamp == 'NULL') and start_timestamp <= ?
                ORDER BY start_timestamp DESC LIMIT 1
                """,(start-10,)
            )
            # 1605827122.8734188, 1605827169.5295694
            # 1605826051.2749164  1605826520.0160236   data point
            # 1605826182.3734622, 1605826182.9516494

            # 1605827106.7947028  new start
            # 1605827067.3296604 NULL  to check
            # 1605826182.9516494 1605827107.3249016  found
            # 1605825533.4479065  to check
            # 1605826182.9516494 = end_of_gap
            

        row = cursor.fetchone()
        tocheck=row[0]
        print("tocheck   ",row[0],row[1])
        cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE (end_timestamp >= ? AND start_timestamp <= ?) AND end_timestamp != 'NULL'
                ORDER BY start_timestamp ASC LIMIT 1
                """,(tocheck,tocheck)
            )
        row = cursor.fetchone()
        if row is not None:
            print("found     ",row[0],row[1])
            start=row[0]
        else:
            print("couldn't find one")

    end_of_gap=start
    print("end_of_gap",end_of_gap)

    cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE end_timestamp != 'NULL' and start_timestamp < ?
                ORDER BY end_timestamp DESC LIMIT 1
                """,(end_of_gap,)
            )
    row = cursor.fetchone()
    start_of_gap=row[0]
    print("str of gap",row[0],row[1])
    print("target gap",start_of_gap,end_of_gap)
    row=True
    skip=False
    while row:
        cursor.execute(
                    f"""
                    SELECT start_timestamp, end_timestamp 
                    FROM wifis
                    WHERE (end_timestamp > ? AND end_timestamp < ?) OR 
                    (start_timestamp > ? AND start_timestamp < ?) OR
                    (start_timestamp < ? AND end_timestamp > ? AND end_timestamp != 'NULL')
                    """,(start_of_gap,end_of_gap,start_of_gap,end_of_gap,start_of_gap,end_of_gap)
                )
        row = cursor.fetchone()
        if row is not None:
            print("found exp ",row[0],row[1])
            if row[0]<start_of_gap:
                if not isinstance(row[1],str):
                    if row[1]> end_of_gap:
                        print("discard this gap")
                        skip=True
                        start=row[0]
                        break
                    if row[1]>start_of_gap:
                        print("start_of_gap=row[1]")
                        start_of_gap=row[1]
            else:
                if not isinstance(row[1],str):
                    if row[1]> end_of_gap:
                        print("end_of_gap=row[1]")
                        end_of_gap=row[1]
                    elif row[1]<end_of_gap:
                        if row[1]-start_of_gap<end_of_gap-row[1]:
                            print("start_of_gap=row[1]")
                            start_of_gap=row[1]
                        else:
                            print("end_of_gap=row[0]")
                            end_of_gap=row[0]
                else:
                    if row[0]-start_of_gap<end_of_gap-row[0]:
                        print("start_of_gap=row[0]   ")
                        start_of_gap=row[0]  
                    else:
                        print("end_of_gap=row[0]   ")
                        end_of_gap=row[0]  
        else:
            print("couldnt find data between ",start_of_gap,end_of_gap) 
                
            # if row[0]-start_of_gap<end_of_gap-row[0]:
            #     # print(row[0]-start_of_gap,end_of_gap-row[0])
            #     if row[1] is not None and not isinstance(row[1],str):
            #         start_of_gap=row[1]
            #     else:
            #         start_of_gap=row[0]
            # else:
            #     end_of_gap=row[0]
            print("gaps      ",start_of_gap,end_of_gap)
    if skip:
        row=[start,None]
        continue
    print("found gaps",start_of_gap,end_of_gap)
    if end_of_gap-start_of_gap<30:
        row=[start_of_gap,end_of_gap]
        print("gap too small, skipping")
        continue
    else:
        gaps.insert(0,[start_of_gap,end_of_gap])

    cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE end_timestamp != 'NULL' and end_timestamp <= ?
                ORDER BY start_timestamp DESC LIMIT 1
                """,(gaps[0][0],)
            )
    row = cursor.fetchone()
    start=row[0]
    
    print("all gaps  ",gaps,"\n")
    print("new start ",start,row[1])

print("gaps",gaps)