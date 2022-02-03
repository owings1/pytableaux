import enum as _enum

__all__ = ()

###### copied from enum module and adjusted attr names for performance.


def _enum_flag_invert(self: _enum.Flag):
    # copied and adapted from
    #   - core enum module, and
    #   - https://github.com/python/cpython/blob/a668e2a1b863f2d/Lib/enum.py
    cached = self._invert_
    value = self._value_
    if cached is not None:
        if cached[0] == value:
            return cached[1]
        self._invert_ = None
    cls = type(self)
    members, uncovered = _enum_flag_decompose(cls, value)
    inverted = cls(0)
    for m in cls:
        if m not in members and not (m._value_ & value):
            inverted = inverted | m
    result = cls(inverted)
    self._invert_ = value, result
    result._invert_ = result._value_, self
    return result

def _enum_flag_decompose(flag: type[_enum.Flag], value: int):
    # copied and adapted from
    #   - core enum module, and
    #   - https://github.com/python/cpython/blob/a668e2a1b863f2d/Lib/enum.py
    # _decompose is only called if the value is not named
    not_covered = value
    negative = value < 0
    members: list[_enum.Flag] = []
    for member in flag:
        member_value = member._value_
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value
    if not negative:
        tmp = not_covered
        while tmp:
            flag_value = 2 ** tmp.bit_length() - 1
            if flag_value in flag._value2member_map_:
                members.append(flag._value2member_map_[flag_value])
                not_covered &= ~flag_value
            tmp &= ~flag_value
    if not members and value in flag._value2member_map_:
        members.append(flag._value2member_map_[value])
    members.sort(key = lambda m: m._value_, reverse = True)
    if len(members) > 1 and members[0]._value_ == value:
        # we have the breakdown, don't need the value member itself
        members.pop(0)
    return members, not_covered

class EnumDictType(_enum._EnumDict):
    'Stub type for annotation reference.'
    _member_names: list[str]
    _last_values : list[object]
    _ignore      : list[str]
    _auto_called : bool
    _cls_name    : str

import sys
if sys.version_info >= (3, 9) and sys.version_info < (3, 11):
    # :-)
    _enum._decompose = _enum_flag_decompose
del(sys)