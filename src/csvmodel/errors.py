class ConfigError(Exception):
    """Something was wrong about the config"""
    pass


class NoSchemaError(Exception):
    """The desired schema was not found"""
    pass
