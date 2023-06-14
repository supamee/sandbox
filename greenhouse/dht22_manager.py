import sqlite3
import os
import numpy as np
from time import time, sleep
from threading import Thread



import adafruit_dht
from board import D4

class DHT22_MAN:
    def __init__(self,path="/dev/shm/data.db",backup_path="/greenhouse/data.db"): 
        self.path=path
        self.backup_path=backup_path
        self.running=True
        self.poll_rate=1
        self.save_rate=120

        self.conn,self.cursor=self.make_table(self.path)
        print("backup db in path:",self.backup_path)
        self.backup_conn,self.backup_cursor=self.make_table(self.backup_path)
        self.conn,self.cursor=self.check_table_works(self.conn,self.cursor)

        working = False
        while not working:
            try:
                self.dht_device = adafruit_dht.DHT22(D4)
                working=True
            except RuntimeError as e:
                print("going to retry",e)
                sleep(3)
            
    
    def make_table(self,path):
        conn = sqlite3.connect(path,check_same_thread=False)

        cursor = conn.cursor()
        conn.execute(
                """
                CREATE TABLE IF NOT EXISTS DHT22 (
                timestamp REAL, 
                temp REAL,
                humidity REAL
                )"""
            )
        return conn,cursor

    
    def check_table_works(self,conn,cursor,wipe=True,gaps=True):
        try:
            conn.execute(
                """
                INSERT INTO DHT22
                (timestamp, temp, humidity)
                VALUES (?, ?, ?)""",
                (
                    time(),
                    None,
                    None
                ),
            )
            sleep(0.1)
            conn.execute(
                """
                INSERT INTO DHT22
                (timestamp, temp, humidity)
                VALUES (?, ?, ?)""",
                (
                    time(),
                    None,
                    None
                ),
            )
            if not gaps:
               conn.execute(
                """
                DELETE FROM DHT22
                WHERE timestamp = 0""",
            )
            conn.commit()
    
        except sqlite3.OperationalError as e:
            print(e)
            if wipe:
                print("deleting data to bypass")
                os.remove("/dev/shm/data.db")
                conn = sqlite3.connect("/dev/shm/data.db",check_same_thread=False)

                cursor = conn.cursor()
                conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS DHT22 (
                        timestamp REAL, 
                        temp REAL,
                        humidity REAL
                        )"""
                    )
            else:
                print("ERROR with database",path)
        return conn,cursor
    
    def take_reading(self):
        data_time=time()
        try:
            temperature = self.dht_device.temperature
            humidity = self.dht_device.humidity
        except Exception as e:
            print("skipped read?",e,type(e))
            temperature=None
            humidity=None
        try:
            self.conn.execute(
                """
                INSERT INTO DHT22
                (timestamp, temp, humidity)
                VALUES (?, ?, ?)""",
                (
                    data_time,
                    temperature,
                    humidity
                ),
            )
            self.conn.commit()
        
            return (data_time,temperature,humidity)
        except Exception as e:
            print("when writing",e,type(e))
            return False

    def backup_data(self):
        xs,temps,humiditys = self.get_old_data()
        if xs:
            last_backup=xs[-1]
        else:
            last_backup=0
        xs,temps,humiditys = self.get_new_data()

        xrun=[]
        trun=[]
        hrun=[]
        for i in range(len(xs)-int(self.save_rate/2)):
            if xs[i]<last_backup:
                continue
            if temps[i]:
                xrun.append(xs[i])
                trun.append(temps[i])
                hrun.append(humiditys[i])
                print("appended data",xs[i],temps[i],humiditys[i])
            elif len(xrun)==0 and not temps[i+1]:
                print("making gap for data at ",xs[i],temps[i],humiditys[i])
                self.backup_conn.execute(
                """
                INSERT INTO DHT22
                (timestamp, temp, humidity)
                VALUES (?, ?, ?)""",
                    (
                        xs[i],
                        None,
                        None
                    ),
                )
                print("-----------------made gap")
                self.backup_conn.commit()
            if xrun and xs[i+1]>xrun[0]+self.save_rate:
                self.conn.execute(
                """
                DELETE FROM DHT22
                WHERE timestamp >= ? and timestamp <= ?""",
                (xrun[0],xrun[-1])
                )
                self.conn.commit()
                
                avg_time=sum(xrun)/len(xrun)
                avg_temp=sum(trun)/len(trun)
                avg_hum=sum(hrun)/len(hrun)
                self.backup_conn.execute(
                """
                INSERT INTO DHT22
                (timestamp, temp, humidity)
                VALUES (?, ?, ?)""",
                    (
                        xrun[-1],
                        avg_temp,
                        avg_hum
                    ),
                )
                print("backed up some data")
                # print(xrun,trun,hrun)
                # print( avg_time,avg_temp,avg_hum)
                self.backup_conn.commit()
                xrun=[]
                trun=[]
                hrun=[]


    def reading_loop(self):
        print("start reading loop")
        last_backup=time()-(self.save_rate/3)
        while self.running:
            self.take_reading()
            print(".",end='')
            sleep(1/self.poll_rate)
            if time()>last_backup+self.save_rate:
                last_backup=time()
                self.backup_data()


    def get_data(self,cursor):
        cursor.execute(
            """
            SELECT timestamp, temp, humidity
            FROM DHT22 
            """,
        )
        pulled_data=cursor.fetchall()
        xs=[]
        temps=[]
        humiditys=[]
        for data_point in pulled_data:
            xs.append(data_point[0])
            temps.append(data_point[1])
            humiditys.append(data_point[2])
        return xs,temps,humiditys

    def get_new_data(self):
        return self.get_data(self.cursor)

    def get_old_data(self):
        return self.get_data(self.backup_cursor)

    def get_all_data(self):
        xs,temps,humiditys = self.get_old_data()
        nxs,ntemps,nhumiditys = self.get_new_data()
        xs.extend(nxs)
        temps.extend(ntemps)
        humiditys.extend(nhumiditys)
        return xs,temps,humiditys