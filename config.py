import configparser


class Config:
    def __init__(self, config_path: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def get(self, section: str, key: str) -> str:
        return self.config.get(section, key)

    def getint(self, section: str, key: str) -> int:
        return self.config.getint(section, key)
