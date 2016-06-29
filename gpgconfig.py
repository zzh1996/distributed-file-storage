import os.path


class gpg_config:
    config_file = 'gpg.config'

    def exist(self):
        return os.path.exists(self.config_file) and os.path.getsize(self.config_file)>0

    def get(self):
        with open(self.config_file) as f:
            content = f.readlines()
            return content[0][:-1],content[1][:-1]

    def set(self, path, email):
        with open(self.config_file, 'w') as f:
            f.write(path+'\n')
            f.write(email+'\n')