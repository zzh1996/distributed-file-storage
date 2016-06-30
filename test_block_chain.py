import blockchain
import dbm
import gpg_wrapper
from protos import dfs_bc_pb2, api_pb2
from vpath.virtual_path import VPath
db = dbm.open('storage.db', 'c')
db[b'height'] = (0).to_bytes(8, byteorder= 'big')
db[b'current_block_hash'] = b'12345'
VPath.bind_to_db(db)
gpg = gpg_wrapper.gpg_object('/home/liu/gpghome', 'test@mydomain.com', 'Security')
print(gpg.fingerprint)
blockchain = blockchain.blockchain(db, gpg)
new_block = blockchain.generate_block_test(b'root_hash')

#print(new_block)
block = new_block
de_passphrase = gpg.decrypt_assym_message(block.struct.sym_key)
print(de_passphrase)
de_root_hash = gpg.decrypt_sym_message(block.struct.root_hash, de_passphrase.decode())
print(de_root_hash)