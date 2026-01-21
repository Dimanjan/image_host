"""
Patch to disable Django's debug SQL logging to avoid conflicts with our SQL formatting.
This prevents Django from trying to format SQL strings with % operator when our SQL uses {} placeholders.
"""

from django.db.backends.sqlite3.operations import DatabaseOperations
from django.db.backends.utils import CursorDebugWrapper

# Store original methods
_original_execute = CursorDebugWrapper.execute
_original_last_executed_query = DatabaseOperations.last_executed_query


def patched_execute(self, sql, params=None):
    """Patched execute that skips debug SQL logging"""
    return self.cursor.execute(sql, params)


def patched_last_executed_query(self, cursor, sql, params):
    """Patched last_executed_query that returns SQL without formatting"""
    # Return SQL as-is without trying to format it
    return sql


# Apply patches
CursorDebugWrapper.execute = patched_execute
DatabaseOperations.last_executed_query = patched_last_executed_query
