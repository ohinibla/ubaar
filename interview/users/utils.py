from datetime import datetime

from django.core.cache import cache

MAX_ATTEMPS = 3
BAN_PERIOD_MINUTE = 60
DEFAULT_USER_STAT = {"attempts": 0, "ban_start_time": None}


def get_ban_remaining_time(identifier):
    """
    Returns remaining ban time saved in cache based on identifier as cache key
    if no cache value found, return a default
    """
    # if `identifier` is None (cache not set yet), don't even check
    if identifier is None:
        return 0
    user_ban_start_time = cache.get(identifier, DEFAULT_USER_STAT).get("ban_start_time")
    # calculate user's remaining ban
    # if user_ban_start_time is None, then the user is not banned, so return 0
    remaining_time_minutes = (
        BAN_PERIOD_MINUTE - (datetime.now() - user_ban_start_time).seconds / 60
        if user_ban_start_time
        else 0
    )
    return remaining_time_minutes


def check_is_user_banned(identifier):
    """
    Returns True if user remaining ban time is other that 0, which
    should mean than user is still banned
    """
    return bool(get_ban_remaining_time(identifier))


def ban_user_if_necessary(identifier):
    """
    Check user attempts and ban it neccessory
    check cache with `identifier` as key for testing user stats
    `identifier` could be username or ip
    set appropriate cache key, value and timeout
    return `if user is banned`
    """
    user_current_stat = cache.get(identifier, DEFAULT_USER_STAT)
    user_attemps = user_current_stat["attempts"]
    user_ban_start_time = user_current_stat["ban_start_time"]
    # the first time user is axceeding the limit, initiate a ban start time.
    if user_attemps == MAX_ATTEMPS:
        user_ban_start_time = datetime.now()
    user_new_stat = {
        "attempts": user_attemps + 1,
        "ban_start_time": user_ban_start_time,
    }
    # calculate the remaining time, if user_ban_start_time is None, then remaining time is
    # the full amount (BAN_PERIOD_MINUTE)
    remaining_time_minutes = (
        BAN_PERIOD_MINUTE - (datetime.now() - user_ban_start_time).seconds / 60
        if user_ban_start_time
        else 0
    )
    # set cache expiry to be BAN_PERIOD_MINUTE
    cache.set(
        identifier,
        user_new_stat,
        timeout=BAN_PERIOD_MINUTE * 60 - remaining_time_minutes,
    )

    return bool(remaining_time_minutes)
