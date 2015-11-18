docker-dovecot-postfix
======================

This is the source to build a Docker image that will let you run temporary IMAP
and SMTP servers sandboxed on your local machine, in a way compatible with
Geary.

Build the Docker image:

    sudo docker build -t mailtest .

Run the image:

    sudo docker run --name mail -d -p 20143:143 -p 20025:25 mailtest
    
    # stop start
    docker stop mail
    sudo docker start mail
    
The image's root password is root, and there's also a normal user named test,
password test.  You can ssh in if you need to examine things.

Mail client:
email: test@example.com
IMAP - host: localhost  port: 20143 encryption : None,  user: test password: test
SMTP - host: localhost  port: 20025 encryption : None,  user: test password: test


Run detach.py as:

		./detach.py -H localhost:20143 --no-ssl -u test -p test  # plus other options


Copyright/License
-----------------

Copyright 2014 Yorba Foundation

This program is free software: you can redistribute it and/or modify it under
the terms of the [GNU General Public
License](http://www.gnu.org/licenses/gpl-3.0.html) as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the [GNU General Public
License](http://www.gnu.org/licenses/gpl-3.0.html) for more details.
