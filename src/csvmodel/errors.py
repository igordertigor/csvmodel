class ConfigError(Exception):
    """Something was wrong about the config"""
    pass


class ValidationError(Exception):
    """Something went wrong when we validated record"""
    def __init__(self, message):
        self.message = message
