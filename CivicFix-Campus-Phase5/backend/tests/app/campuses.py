"""Fixed campus registry.

Campuses are configuration, not user input: a real deployment would manage
these from an admin screen or a database collection, but for a college
prototype a short fixed list keeps the isolation logic easy to audit.
"""

CAMPUSES = [
    {"id": "main-campus", "name": "Main Campus"},
    {"id": "north-campus", "name": "North Gate Campus"},
]

_BY_ID = {campus["id"]: campus["name"] for campus in CAMPUSES}


def campus_name(campus_id: str) -> str:
    return _BY_ID.get(campus_id, campus_id)


def is_valid_campus(campus_id: str) -> bool:
    return campus_id in _BY_ID
