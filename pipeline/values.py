"""Small validation primitives shared by the paper pipeline's trust boundaries."""

from decimal import Decimal, InvalidOperation
import hashlib
import json


def number(value, *, signed=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)) or len(str(value)) > 100:
        raise ValueError("Invalid decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid decimal") from error
    if not result.is_finite() or len(result.as_tuple().digits) > 40 or not -24 <= result.as_tuple().exponent <= 24:
        raise ValueError("Decimal outside supported bounds")
    if result.copy_abs() > Decimal("1e24") or (not signed and result < 0):
        raise ValueError("Invalid decimal range")
    return result


def stamp(value):
    if type(value) is not int or not 0 <= value < 2**63 - 1:
        raise ValueError("Invalid UTC timestamp")
    return value


def identity(prefix, value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return prefix + hashlib.sha256(data).hexdigest()
