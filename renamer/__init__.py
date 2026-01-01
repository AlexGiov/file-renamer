"""
File Renamer Tool - Clean Architecture Implementation.

This package provides a professional-grade file renaming tool following SOLID principles,
implementing cross-platform safe naming conventions per RENAMER.md specification.

Public API:
    - FileRenamerFactory: Factory for creating renamer instances with DI
    - RenameResult: Immutable result value object
    - FileRenamerProtocol: Protocol interface for renamers
"""

from .factory import FileRenamerFactory
from .domain.models import RenameResult, OperationStats
from .protocols import FileRenamerProtocol

__all__ = [
    'FileRenamerFactory',
    'RenameResult',
    'OperationStats',
    'FileRenamerProtocol',
]

__version__ = '2.0.0'
