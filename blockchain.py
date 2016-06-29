from __future__ import division

import sys

sys.path.append('protos')
import dfs_bc_pb2, api_pb2
import gpg_wrapper
from grpc.beta import implementations
import hashlib
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from functools import reduce


class blockchain(api_pb2.BetaBlockChainServicer):
    db_lock = Lock()
    java_forward_host = 'localhost'
    java_forward_port = 5002

    def __init__(self, db, gpg_object):
        """

        :param db:
        :param gpg_object:
        """
        self.db = db
        self.gpg_object = gpg_object
        self.height = db[b'height']
        self.PK = gpg_object.fingerprint
        self.current_block_hash = db[b'current_block_hash']

    @classmethod
    def get_hash(cls, block):
        h = hashlib.sha256()
        h.update(block.SerializeToString())
        return h.digest()

    def send_request_inquiry(self):
        """

        :return: bytes request_inquiry
        """

        def _cmp(x, y):
            if not x:
                return False
            if x.hashes == y.hashes:
                return x
            else:
                return False

        request_inquiry = api_pb2.request_inquiry()
        request_inquiry.height = self.height
        request_inquiry.current_block_hash = self.current_block_hash

        res = self.stub.request_inquiry_forward(request_inquiry)
        if len(res) < 1:
            raise ValueError("No Response")

        max_len = max(map(lambda x: len(x.hashes), res))
        q = list(filter(lambda x: len(x.hashes) == max_len, res))
        if len(q) == 1:
            equal = True
        else:
            equal = reduce(q, _cmp)
        with ThreadPoolExecutor(max_workers=4) as executor:
            if not equal:
                executor.submit(self.send_sync_req, q[0].id, q[0].hashes)
                pass
            else:
                start = 0
                l = ceil(max_len / len(q))
                for res in q:
                    executor.submit(self.send_sync_req, res.id, res.hashes[start:start + l])
                    start += l
            executor.shutdown(wait=True)

        return request_inquiry

    def receive_request_inquiry(self, request_inquiry, context):
        """

        :param request_inquiry: default is None
        :param context:
        :return: respond_inquiry. If hashes are not None, the newer block-hash has smaller index
        """
        respond_inquiry = api_pb2.response_inquiry()
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
                # prevent parent block is None
                assert self.db[block.parent]
                block = self.db[block.parent]
            respond_inquiry.forking = False
        return respond_inquiry

    def commit_block_local(self, block):
        self.db_lock.acquire()
        self.current_block_hash = self.get_hash(block)
        self.db[self.current_block_hash] = block
        self.db[b'current_block_hash'] = self.current_block_hash
        self.height = self.height + 1
        self.db[b'height'] = self.height

    def generate_block(self, root_hash, payload_hash=b''):
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
        fingerprint, enc_root_hash, passphrase = \
            gpg_wrapper.blockchain_encrypt(
                root_hash,
                self.gpg_object.homedir,
                self.gpg_object.email_address,
                self.gpg_object.key_passphrase
            )
        block.struct.root_hash = enc_root_hash
        block.struct.sym_key = passphrase
        block.signature = self.gpg_object.sign_message(
            block.struct.SerializeToString()
        )
        self.db_lock.acquire()
        self.commit_block_local(block)
        # propel block to other node
        self.propel_block(block)
        # wait for confirm of the new block
        # response_push.confirm is True
        self.db_lock.release()
        return block

    def propel_block(self, block):
        """
        push_block
        :param dfs_bc_pb2.Block block:
        :return: bool if push is accepted
        """
        return True

    def send_sync_req(self, id, hashes):

        req = api_pb2.request_syn()
        req.id = id
        req.hashes = hashes
        ch = implementations.insecure_channel(self.java_forward_host, self.java_forward_port)
        stub = api_pb2.beta_create_JavaForward_stub(ch)
        return stub.request_syn_forward(req)

    def receive_request_syn(self, req, context):

        res = api_pb2.response_syn()
        for h in req.hashes:
            res.hash = h
            res.block = self.db[h].SerializeToString()
            yield res


def serve(db, gpg_object):
    import time, os
    server = api_pb2.beta_create_BlockChain_server(blockchain(db, gpg_object))
    port = os.getenv('PORT') or 5001
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()
    _ONE_DAY_IN_SECONDS = 60 * 60 * 24
    try:
        while 1:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
