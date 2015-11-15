* Implement additional filters
	
	* add ^= starts with comparison and $= ends with
	* Add date filter ( in imap BEFORE ON SINCE)
	* Add size filter ( imap can help only with LARGER)
	* Add body part number to filter
* Update part size based on encoding (or disposition?)
* Python 2 compatibility
* Check case insensivity when processing message headers
* Test imap  BODY TEXT search -  can it search mime, filename?
* Delete, mark seen, move email after downloading
* Run command on downloaded email -  file piped to stdin
* UTF-8 support in IMAP search subject
* Multithreaded (multiprocess?)  download
* Improve BODYSTRUCTURE parting to go into message/rfc822
* Refactor imap_client into 2 modules


	