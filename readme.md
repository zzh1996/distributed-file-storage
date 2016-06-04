##Distributed file storage (Python, v3)

###Requirements:
 - flask
 - protobuf3
 - gnupg
installation via pip:
```bash
$ pip3 install flask
$ pip3 install protobuf==3.0.0b3
$ pip3 install gnupg
```

###Modules
 - vpath
 - web server
 - blockchain(todo)
 
 ###Introduction
 
We've implemented a local version control, which supports indexing, adding, and deleting files ,storing changes in the buffer, as well as  committing to the remote file system. The encrypted hash of root directory will be consisted in the blockchain nodes, broadcast to other nodes.
For cryptography, we use GnuPG both in blockchain node structure and file sharing for simple handling and high security.
