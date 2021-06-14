class CancellationException(Exception):
    """
    Exception used for injecting a cancellation into python steps execution.
    """

    def __init__(self, message="Execution was cancelled (injected in test)"):
        self.message = message
        super().__init__(self.message)
