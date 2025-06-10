"""
Custom exceptions for the Fylex Library.
"""

class FylexError(Exception):
    """Base exception"""
    pass
    
class InvalidPathError(FylexError):
    """Raised in case of non-existent paths"""
    def __init__(self, path, message = None):
        if message is None:
            message = f"Invalid or inaccessible path given: {path}"
            super().__init__(message)
            self.path = path

class PermissionDeniedError(FylexError):
    """Raised when the program lacks permission to read/write a file."""
    def __init__(self, path, operation="access"):
        message = f"Permission denied while attempting to {operation}: {path}"
        super().__init__(message)
        self.path = path
        self.operation = operation
