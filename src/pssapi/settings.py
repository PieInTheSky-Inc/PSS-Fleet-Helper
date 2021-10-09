import os as _os



ACCESS_TOKEN: str = _os.environ.get('PSS_ACCESS_TOKEN')


DEFAULT_PSS_PRODUCTION_SERVER: str = 'api.pixelstarships.com'


OVERWRITE_PSS_PRODUCTION_SERVER: str = _os.environ.get('PSS_PRODUCTION_SERVER')