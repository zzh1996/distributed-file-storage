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
Notice:

 1. Beware of the version of protobuf and grpc.
 2. We have compiled our protobuf and put the latest generated code in this repository. To recompile, the protobuf compiler and grpc_python_plugin is needed. Please refer to [protobuf project](https://github.com/google/protobuf) and [grpc project](https://github.com/grpc/grpc).
 3. Grpc python runtime(pip package) requires grpc_python_plugin and the protoc compiler(consulting to Notice:2). Don't forget to add them to $PATH
 4. To setup java runtime, please refer to README.md by XuQiang's group.
 5. Our group is responsible for starting XuQiang's java at startup, while we assume their REOpenChord directory locates at the same level as ours.

### Modules
 - VPath
 - Web server
 - Blockchain(almost done, haven't test)

### Introduction

We've implemented a local index(version control?), which supports `indexing`, `adding`, and `deleting` files, as well as storing changes in the buffer and committing them to the remote file system.

The encrypted hash of the root directory consists in the Blockchain nodes, broadcasted to other nodes.

For cryptography, we use GnuPG both in Blockchain node structure and file sharing for simple handling and high security.
