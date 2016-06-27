ifndef PROTOC
	PROTOC=protoc
endif
ifndef PY_PLUGIN
	PY_PLUGIN=`which grpc_python_plugin`
endif
ifndef JAVA_PLUGIN
	JAVA_PLUGIN=`which protoc-gen-grpc-java`
endif
all: api dfs_bc dirinfo
api: api.proto
	${PROTOC} --plugin=protoc-gen-grpc-java=${JAVA_PLUGIN} --grpc-java_out=. --java_out=. api.proto
	${PROTOC} --plugin=grpc_python_plugin=${PY_PLUGIN} --python_out=. api.proto
dfs_bc: dfs_bc.proto
	${PROTOC} --python_out=. dfs_bc.proto

dirinfo: dirinfo.proto
	${PROTOC} --python_out=. dirinfo.proto

clean:
	-rm -rf api_pb2.py cn/ dfs_bc_pb2.py dirinfo_pb2.py
