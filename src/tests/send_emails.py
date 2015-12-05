import smtplib
from email.mime.text import MIMEText
import re
import random
from six import print_ as p
import sys
import time

text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, 
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut 
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate 
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non 
proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

words = re.split(r'\s*\.?,?\s*', text)

def rand_text():
    size=random.randint(len(words)/2, len(words))    
    t=random.sample(words,size)
    return ' '.join(t)


count=int(sys.argv[1]) if len(sys.argv)>1 else 1

s = smtplib.SMTP('localhost', port=20025)
s.login('test', 'test')
for i in range(count):
    msg = MIMEText(rand_text())
    # you == the recipient's email address
    msg['Subject'] = 'Test Email %d'%i
    msg['From'] = 'test@example.com'
    msg['To'] = 'test@example.com'
    s.sendmail('test@example.com', ['test@example.com'], msg.as_string())
    p('Sent email no. %d'%i)
    time.sleep(0.1)
    
s.quit()