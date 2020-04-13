#!/usr/bin/env python3

"""
Various useful functions.
"""


import struct


def segment_intersect(segment1, segment2):
    """
    Return whether two segments intersect.
    """
    ((x1, y1), (x2, y2)) = segment1
    ((x3, y3), (x4, y4)) = segment2
    num = 1.0*(x4-x3)*(y1-y3)-(y4-y3)*(x1-x3)
    den = 1.0*(y4-y3)*(x2-x1)-(x4-x3)*(y2-y1)
    if den == 0:
        return num == 0
    return 0 <= (num / den) <= 1



MSGLEN = 24

def encode_message(_id, x, y, angle, angleturret, fire):
    """
    Binary encode 4 integer.
    """
    if fire:
        fireInt = 1
    else:
        fireInt = 0
    return struct.pack('iiiiii', _id, x, y, angle, angleturret, fireInt)


def decode_message(data):
    """
    Binary decode 4 integers.
    """
    _id, x, y, angle, angleturret, fireInt = struct.unpack('iiiiii', data)
    return _id, x, y, angle, angleturret, (fireInt == 1)
