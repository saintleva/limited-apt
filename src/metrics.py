import math


def pretty_size(byte_count):
    r"""Returns pretty size (in kilobytes, megabytes etc.)
    
    'byte_count' parameter must be non-negative
    
    >>> pretty_size(-1)
    Traceback (most recent call last):
        ...
    AssertionError: size in negative
    >>> pretty_size(0)
    ('B', 0)
    >>> pretty_size(999)
    ('B', 999)
    >>> pretty_size(999999)
    ('MB', 1)
    >>> pretty_size(341293)
    ('KB', 341)
    >>> pretty_size(289341293)
    ('MB', 289)
    >>> pretty_size(9999999999999999999)
    ('TB', 10000000)
    """
    
    assert byte_count >= 0, "size in negative"
    
    if byte_count == 0:
        return "B", 0
    
    metric_prefixes = ["B", "KB", "MB", "GB", "TB"]
    kilo = 1000
    current_quantity = byte_count
    cls = 0
    
    while math.log10(current_quantity) >= 4 and cls < len(metric_prefixes) - 1:
        current_quantity /= kilo
        cls += 1
        
    if round(current_quantity) == kilo and cls < len(metric_prefixes) - 1:
        current_quantity /= kilo
        cls += 1
                
    return metric_prefixes[cls], round(current_quantity)


def pretty_size_str(byte_count):
    prefix, size = pretty_size(byte_count)
    return str(size) + prefix

               
if __name__ == '__main__':
    import doctest
    doctest.testmod()