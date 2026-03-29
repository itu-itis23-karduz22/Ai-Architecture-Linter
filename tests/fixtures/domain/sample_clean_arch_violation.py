"""Sample Python file with Clean Architecture violation (used in tests).

This file lives in a 'domain' (entities) layer but imports from 'infrastructure'.
"""
# This import violates Clean Architecture: inner layer → outer layer
from infrastructure.database import UserRepository  # noqa: F401
from infrastructure.external import PaymentGateway   # noqa: F401
