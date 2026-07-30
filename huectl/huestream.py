"""HueStream v2 frame protocol (Philips Hue Entertainment).

A frame is a 52-byte header followed by 7 bytes per channel:

    "HueStream"                     9 bytes ASCII
    version                         2 bytes  (0x02, 0x00)
    sequence id                     1 byte
    reserved                        2 bytes  (0x00, 0x00)
    color space                     1 byte   (0x00 = RGB, 0x01 = xy+brightness)
    reserved                        1 byte   (0x00)
    entertainment configuration id  36 bytes ASCII (UUID)
    per channel:
        channel id                  1 byte
        color                       6 bytes  (3 x uint16, big-endian)

Colors are 16-bit. Helpers convert from 8-bit RGB.
"""

import struct

MAGIC = b"HueStream"
COLOR_RGB = 0x00
COLOR_XY = 0x01


def rgb8_to_16(r, g, b):
    """8-bit (0..255) -> 16-bit (0..65535), preserving full range."""
    return (r * 257, g * 257, b * 257)


def build_frame(config_id, channels, seq=0, color_space=COLOR_RGB):
    """Build one HueStream v2 datagram.

    config_id: 36-char entertainment configuration UUID.
    channels:  iterable of (channel_id, (c0, c1, c2)) with 16-bit components.
    """
    cid = config_id.encode("ascii")
    if len(cid) != 36:
        raise ValueError("entertainment configuration id must be 36 chars")
    header = MAGIC + bytes([0x02, 0x00, seq & 0xFF, 0x00, 0x00,
                            color_space & 0xFF, 0x00]) + cid
    body = bytearray()
    for ch_id, (c0, c1, c2) in channels:
        body += bytes([ch_id & 0xFF]) + struct.pack(">HHH", c0, c1, c2)
    return bytes(header) + bytes(body)


def build_rgb_frame(config_id, channel_colors, seq=0):
    """Convenience: channel_colors = iterable of (channel_id, (r8, g8, b8))."""
    chans = [(cid, rgb8_to_16(*rgb)) for cid, rgb in channel_colors]
    return build_frame(config_id, chans, seq=seq, color_space=COLOR_RGB)
