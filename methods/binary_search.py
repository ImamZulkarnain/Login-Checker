"""Sort usernames with merge sort, then look them up with binary search."""

def merge(left_usernames, right_usernames):
    """Take two sorted lists and return one sorted list containing their entries."""
    merged_usernames = []
    left_index = 0
    right_index = 0

    # Compare the next username from each list and take the smaller one.
    while left_index < len(left_usernames) and right_index < len(right_usernames):
        left_username = left_usernames[left_index]
        right_username = right_usernames[right_index]

        if left_username <= right_username:
            merged_usernames.append(left_username)
            left_index += 1
        else:
            merged_usernames.append(right_username)
            right_index += 1

    # One list may still have usernames left after the other runs out.
    while left_index < len(left_usernames):
        merged_usernames.append(left_usernames[left_index])
        left_index += 1

    while right_index < len(right_usernames):
        merged_usernames.append(right_usernames[right_index])
        right_index += 1

    return merged_usernames


def merge_sort(usernames):
    """Take a username list and return its entries in case-sensitive sorted order.

    Split the list into halves, sort each half, and merge the sorted halves.
    The input list is not modified. Empty and single-entry lists are returned
    directly because they are already sorted.
    """
    if len(usernames) <= 1:
        return usernames

    middle = len(usernames) // 2

    # A slice selects the entries before or after the middle position.
    left_half = usernames[:middle]
    right_half = usernames[middle:]

    sorted_left = merge_sort(left_half)
    sorted_right = merge_sort(right_half)

    sorted_usernames = merge(sorted_left, sorted_right)
    return sorted_usernames


def binary_search(usernames, target):
    """Take a sorted username list and target; return True if found, else False.

    The list must use the same case-sensitive order as merge_sort.
    Each comparison removes half of the remaining search range.
    """
    left = 0
    right = len(usernames) - 1

    while left <= right:
        middle = (left + right) // 2
        middle_username = usernames[middle]

        if middle_username == target:
            return True
        elif target < middle_username:
            right = middle - 1
        else:
            left = middle + 1

    return False
