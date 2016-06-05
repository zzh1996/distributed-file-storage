import gnupg
import tempfile
import io
import os
import pprint


class gpg_key(object):
    def __init__(self, homedir):
        self.homedir = homedir
        self.gpg = gnupg.GPG(homedir= homedir)

    def generate_key(self, input_data):
        """

        :param dict input_data:
            input_data= {
                'key_type' : 'RSA',
                'key_length': 1024,
                'key_usage': 'ESCA',
                'subkey_type':'RSA',
                'subkey_length':1024,
                'subkey_usage':'encrypt,sign,auth',
                'name_email':'test@mydomain.com',
                'passphrase': 'passphrase'
            }
        :return: key
        """
        input = self.gpg.gen_key_input(**input_data)
        key = self.gpg.gen_key(input)

    def import_keyid_fingerprint(self, email_address):
        """
        import the fingerprint of relevent email_address
        :return: str fingerprint
        """
        pubkeys = self.gpg.list_keys()
        for item in pubkeys:
            if email_address in item['uids'][0]:
                return item['fingerprint']

    def list_public_keys(self):
        pprint.pprint(self.gpg.list_keys())

    def import_public_key(self, public_key):
        self.gpg.import_keys(public_key)

    def export_public_key(self, email_address):
        """

        :return: str public_key
        """
        fingerprint = self.import_keyid_fingerprint(email_address)
        public_key = self.gpg.export_keys(fingerprint)
        return public_key

    def delete_key(self, email_address):
        pubkeys = self.gpg.list_keys()
        for item in pubkeys:
            if email_address in item['uids'][0]:
                self.gpg.delete_keys(item['fingerprint'], True)
                self.gpg.delete_keys(item['fingerprint'], subkeys=True)


class gpg_object(object):
    def __init__(self, homedir, email_address, key_passphrase):
        self.homedir = homedir
        self.email_address = email_address
        self.key_passphrase= key_passphrase
        self.gpg = gnupg.GPG(homedir=self.homedir)
        self.fingerprint= self.import_keyid_fingerprint()

    def import_keyid_fingerprint(self):
        """
        import the fingerprint of relevent email_address
        :return: str fingerprint
        """
        pubkeys = self.gpg.list_keys()
        for item in pubkeys:
            if self.email_address in item['uids'][0]:
                return item['fingerprint']

    def encrypt_sym_message(self, message, passphrase):
        """
        encrypt the message with passphrase symmetrically
        :param bytes message:
        :param str passphrase:
        :return: bytes encrypted_data
        """
        encrypted_data = self.gpg.encrypt(
            message,
            self.fingerprint,
            encrypt= False,
            passphrase = passphrase,
            symmetric = True
        )
        assert encrypted_data.ok== True
        assert str(encrypted_data)!= message
        assert not str(encrypted_data).isspace()
        return encrypted_data.data

    def decrypt_sym_message(self, message, passphrase):
        """
        decrypt the symmetrically encrypted message
        :param bytes message:
        :param str passphrase:
        :return:  bytes decrypted_data
        """
        decrypted_data = self.gpg.decrypt(message, passphrase=passphrase)
        assert not str(decrypted_data).isspace()
        return decrypted_data.data

    def encrypt_assym_message(self, message):
        """
        encrypt the message with passphrase assymmetrically
        :param bytes message:
        :return:  bytes encrypted_data
        """
        encrypted_data = self.gpg.encrypt(message, self.fingerprint)
        assert str(encrypted_data) != message
        assert not str(encrypted_data).isspace()
        return encrypted_data.data

    def decrypt_assym_message(self, message):
        """
        decrypt the assymmetrically encrypted message
        :param bytes message:
        :return:  bytes decrypted_data
        """
        decrypted_data = self.gpg.decrypt(message, passphrase = self.key_passphrase)
        assert not str(decrypted_data).isspace()
        return decrypted_data.data

    def sign_message(self, message, digest_algo='sha256'):
        """
        sign message
        :param bytes message:
        :param digest_algo: the algorithem used to digest
        :return: bytes signature
        """
        signature= self.gpg.sign(
            message,
            default_key= self.fingerprint,
            passphrase= self.key_passphrase,
            digest_algo= digest_algo,
            clearsign= False,
            detach= True
        )
        assert signature
        return signature.data

    def verify_signature(self, message, signature):
        """

        :param bytes message:
        :param bytes signature:
        :return:
        """
        message_io = io.BytesIO(message)
        tmp = tempfile.mkstemp()
        fp = open(tmp[1],'wb')
        fp.write(signature)
        fp.close()
        verify= self.gpg.verify_file(message_io, tmp[1])
        os.close(tmp[0])
        os.remove(tmp[1])
        return(verify.valid)

def blockchain_encrypt(roothash, homedir, email_address, passphrase):
    """

    :param bytes roothash:
    :param homedir:
    :param email_address:
    :param passphrase:
    :return: (fingerprint, sym_encrypted_data, assym_encrypted_passphrase)
    """
    gpg = gpg_object(homedir, email_address, passphrase)
    passphrase = gnupg._util._make_random_string(32)
    #generate a symmetric encrypt towards passphrase
    sym_encrypted_data= gpg.encrypt_sym_message(roothash, passphrase)
    # generate a assymmetric encrypt on passphrase
    assym_encrypted_passphrase= gpg.encrypt_assym_message(passphrase)
    return (gpg.fingerprint, sym_encrypted_data , assym_encrypted_passphrase)
