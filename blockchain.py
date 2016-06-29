import sys
sys.path.append('protos')
import dfs_bc_pb2, api_pb2
import gpg_wrapper
from grpc.beta import implementations

class blockchain(api_pb2.BetaBlockChainServicer):
    def __init__(self, db, PK):
        """

        :param db:
        :param PK:
        """
        self.db = db
        self.height = db['height']
        self.PK = PK
        self.current_block_hash = db['current_block_hash']

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

        :param respond_inquiry:
        :return:(id, hashes)
        """
        return

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

