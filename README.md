## Distributed File Storage (Python, v3)

### Requirements:
 - flask
 - protobuf3
 - grpc release 0.15
 - gnupg

Installation via pip:
```bash
$ pip3 install flask
$ pip3 install protobuf==3.0.0b3
$ pip3 install gnupg
$ pip3 install grpc==0.15.0
```

### Modules
 - Vpath
 - Web server
 - Blockchain(work in progress)

### Introduction

We've implemented a local index(version control?), which supports `indexing`, `adding`, and `deleting` files, as well as storing changes in the buffer and committing them to the remote file system.

The encrypted hash of the root directory consists in the Blockchain nodes, broadcasted to other nodes.

For cryptography, we use GnuPG both in Blockchain node structure and file sharing for simple handling and high security.
