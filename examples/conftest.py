def redis_kwargs_for_test():
    return dict(
        host="127.0.0.1",
        port=6379,
        db=0,
        password=None,
        decode_responses=False,
        socket_connect_timeout=None,
    )
