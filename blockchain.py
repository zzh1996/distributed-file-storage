import sys
sys.path.append('protos')
import dfs_bc_pb2, api_pb2
import gpg_wrapper
from grpc.beta import implementations
import hashlib
from threading import Lock

class blockchain(api_pb2.BetaBlockChainServicer):
    db_lock = Lock()
    def __init__(self, db, gpg_object):
        """

        :param db:
        :param PK:
        """
        self.db = db
        self.gpg_object = gpg_object
        self.height = db[b'height']
        self.PK = gpg_object.fingerprint
        self.current_block_hash = db[b'current_block_hash']

    def get_hash(self, block):
        h = hashlib.sha256()
        h.update(block.SerializeToString())
        return h.digest()


    def send_request_inquiry(self):
        """

        :return: bytes request_inquiry
        """
        request_inquiry = api_pb2.request_inquiry()
        request_inquiry.height = self.height
        request_inquiry.current_block_hash = self.current_block_hash
        return request_inquiry

    def receive_request_inquiry(self, request_inquiry, context):
        """

        :param request_inquiry: default is None
        :param context:
        :return: respond_inquiry. If hashes are not None, the newer block-hash has smaller index
        """
        respond_inquiry = api_pb2.respond_inquiry()
        re_height = request_inquiry.height
        re_current_block_hash = request_inquiry.current_block_hash
        if re_height < self.height and re_current_block_hash not in self.db:
            respond_inquiry.forking = True
        elif re_height > self.height and re_current_block_hash not in self.db:
            respond_inquiry.forking = False
            self.send_request_inquiry()
        elif re_height < self.height and re_current_block_hash in self.db:
            block = dfs_bc_pb2.Block()
            block.ParseFromString(self.db[self.current_block_hash])
            while re_current_block_hash != block.parent:
                respond_inquiry.hashes.append(block.parent)
                #prevent parent block is None
                assert self.db[block.parent]
                block = self.db[block.parent]
            respond_inquiry.forking = False
        return respond_inquiry



    def generate_block(self, root_hash, payload_hash = b''):
        """

        :param bytes root_hash:
        :param bytes payload_hash:
        :return:
        """
        block = dfs_bc_pb2.Block()
        block.struct.PK = self.PK
        block.struct.parent = self.current_block_hash
        block.struct.height = self.height + 1
        block.struct.payload_hash = payload_hash
        fingerprint, hash, passphrase = \
            gpg_wrapper.blockchain_encrypt(
                root_hash,
                self.gpg_object.homedir,
                self.gpg_object.email_address,
                self.gpg_object.key_passphrase
            )
        block.struct.root_hash = hash
        block.struct.sym_key = passphrase
        block.signature = self.gpg_object.sign_message(
            block.struct.SerializeToString()
        )
        self.db_lock.acquire()
        self.current_block_hash = self.get_hash(block)
        self.db[self.current_block_hash] = block
        self.db[b'current_block_hash'] = self.current_block_hash
        self.height = self.height + 1
        self.db[b'height'] = self.height
        self.db_lock.release()
        return block

    #def propel_block(self, block):

    def send_sync_req(self, id, hashes):

        req = api_pb2.request_sync()
        req.id = id
        req.hashes = hashes
        ch = implementations.insecure_channel('localhost', self.port)
        stub = api_pb2.beta_create_JavaForward_stub(ch)
        return stub.request_syn_forward(req)

    def receive_request_syn(self, req):

        res = api_pb2.response_syn()
        for h in req.hashes:
            res.hash = h;
            res.block = self.db[h].SerializeToString()
            yield res

def serve():
    import time, os
    server = api_pb2.beta_create_BlockChain_server(blockchain)
    port = os.getenv('PORT') or 8080
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()
    _ONE_DAY_IN_SECONDS = 60 * 60 * 24
    try:
        while 1:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()

