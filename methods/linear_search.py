""" check a username using linear search."""

def linear_search(usernames, target):
    """Take a username list and target; return True if found, otherwise False."""
    for username in usernames:
        if username == target:
            return True

    return False
