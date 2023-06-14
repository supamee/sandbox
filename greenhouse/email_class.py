#!/usr/bin/python

import smtplib
class Emailer:
    def __init__(self,sender='coatsforgoats38@gmail.com',user='coatsforgoats38',password='wfgopkaunshchyze'):
        self.sender=sender 
        self.user=user
        self.password=password
        self.smtpObj = smtplib.SMTP('smtp.gmail.com', port=587)
        self.smtpObj.starttls()
        self.smtpObj.login(user, password)
    
    def send(self,dst,body="This is a test e-mail message.",subject="SMTP e-mail test"):
        message = """From: Coats For Goats <from@fromdomain.com>
To: """+dst[0]+"""
Subject: """+subject+"""

"""+body+"""
"""
        self.smtpObj.sendmail(self.sender, dst, message)  
        print("sent email") 

