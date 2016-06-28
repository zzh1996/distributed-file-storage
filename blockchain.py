import dfs_bc_pb2
import api_pb2
import gpg_wrapper
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
