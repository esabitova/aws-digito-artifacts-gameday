class NonRetriableException(Exception):
    """
    Exception used for marking execution failure that should not be retried.
    If this exception is used, no further attempts will be made (even if max_attempts have not been attempted)
    """
