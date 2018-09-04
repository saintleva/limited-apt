#!/usr/bin/env python3

import math


def pretty_size(bytes):
    if bytes == 0:
        return "B", 0
    
    metric_prefixes = ["B", "KB", "MB", "GB", "TB"]
    kilo = 1000
    current_quantity = bytes
    cls = 0
    
    while math.log10(current_quantity) >= 3:
        print("current_quantity == {0}".format(current_quantity))
        current_quantity /= kilo
        cls += 1
        
    if round(current_quantity) == kilo:
        current_quantity /= kilo
        cls += 1
        
    return metric_prefixes[cls], round(current_quantity)
 
        
def main():
    print(pretty_size(999999999999999))

        
if __name__ == '__main__':
    main()