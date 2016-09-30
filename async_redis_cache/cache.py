class BaseCache:

    def __init__(self, client, serializer):
        self.client = client
        self.servers = []
        self.serializer = serializer

    def add(self, key, value):
        """
        Add a value to the cache, if the key exists it fails.

        :param key: str
        :param value: obj
        :raises: ValueError
        """
        raise NotImplementedError

    def get(self, key, default=None, serializer=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj
        :param serializer: Optional serializer object to use. Must have the deserialize function
        :returns: obj deserialized
        """
        raise NotImplementedError

    def set(self, key, value, timeout=None, serializer=None):
        """
        Stores the value in the given key with timeout if specified

        :param key: str
        :param value: obj
        :param timeout: int the expiration time in seconds
        :param serializer: Optional serializer object to use. Must have the serialize function
        :returns:
        """
        raise NotImplementedError

    def delete(self, key):
        """
        Remove key from the cache

        :param key: str
        """
        raise NotImplementedError

    def incr(self, key, count=1):
        """
        Add count to the given key. If key does not exist it creates it and sets it to count

        :param key: str
        :param count: int
        """
        raise NotImplementedError

    def expire(self, key, timeout):
        """
        Sets timeout to the given key

        :param key: str
        :param timeout: int the expiration time in seconds
        """
        raise NotImplementedError

    def ttl(self, key):
        """
        Returns the time to live of a key in seconds.

        :param key: str
        :returns: time to live in seconds
        """
        raise NotImplementedError

    def persist(self, key):
        """
        Remove the timeout for a key.

        :param key: str
        """
        raise NotImplementedError

    def get_or_set(self, key, value, timeout=None, serializer=None):
        """
        Tries to retrieve a key. If not existing it creates setting the specified value.
        Applies timeout and uses the given serializer if they are passed.

        :param key: str
        :param value: obj
        :param timeout: int the expiration time in seconds
        :param serializer: Optional serializer object to use. Must have the serialize function
        :returns: obj deserialized, True|False if created
        """
        raise NotImplementedError
