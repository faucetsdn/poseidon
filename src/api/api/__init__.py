from pbr.version import VersionInfo

# TODO: 3.8+ and later, use importlib: https://pypi.org/project/importlib-metadata/
__version__ = VersionInfo('poseidon_api').semantic_version().release_string()
