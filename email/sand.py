#!/usr/bin/python

import smtplib

sender = 'coatsforgoats38@gmail.com'
# receivers = ['19209187619@vtext.com','19209187619@vzwpix.com','19209187619@txt.att.net','19209187619@tmomail.net','19209187619@messaging.sprintpcs.com']
receivers = ['9209187619@txt.att.net'] #each carrier had their own web address
receivers = ['user@gmail.com']

user='coatsforgoats38'
password='wfgopkaunshchyze'

id="112162518469-kipm7f21n01f11jqhb4sb7a73krtimbu.apps.googleusercontent.com"
key="lrzLeAFoHqSxALFPVad6yTYn"

message = """From: From Person <from@fromdomain.com>
To: To Person <to@todomain.com>
Subject: SMTP e-mail test

This is a test e-mail message.
"""

# try:
smtpObj = smtplib.SMTP('smtp.gmail.com', port=587)
smtpObj.starttls()
smtpObj.login(user, password)
smtpObj.sendmail(sender, receivers, message)         
print ("Successfully sent email")
# except SMTPException:
#    print( "Error: unable to send email")