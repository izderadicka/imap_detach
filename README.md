**imap_detach** is utility for automatic downloading of email attachments from email box via IMAP protocol.

Messages' attachments are specified by simple logical expressions like
```
mime="application/pdf" & to ~= "myself"
```
this will download all pdf files where to address contains myself
```
attached & ! seen
```
this will download all attachments that have not been seen yet by email client
```
(from ~= "john" | from ~= "dave") & mime ~= "image"
```
this will download all images sent by john or dave


Filename of save files can contain replacement strings, so for instance /home/myself/Downloads/email/{from}/{name} 
will create directories for sender and save there attachments under their file name defined in the email 
(assuming these are attachments, which need to be specified in filter)

Similarly downloaded message part can be used in command -  either through standard input or with 
replacement string {file_name} and other replacements valid output file as described above.

For help use detach.py -h 

Currently beta quality code, tested in python 3.4 and 2.7.

LICENSE
-------
GPL v3