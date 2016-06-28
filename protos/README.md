### Define protos

#### Content

- **api.proto** communication with java, include both filesystem api and blockchain api
- **dfs_bc.proto** structure of blockchain
- **dirinfo.proto** structure of the index of virtual filesystem

#### Generate Code

```
#generate all
make

OR

make api
make dirinfo
make dfs_bc

```
customize protoc and plugin
set the env PROTOC, PY_PLUGIN, JAVA_PLUGIN to corresponding path

```
#example
PROTOC=../../protobuf/src/protoc PY_PLUGIN=../../grpc/bins/opt/grpc_python_plugin  JAVA_PLUGIN=../../grpc/bins/opt/protoc-gen-grpc-java make api

```
