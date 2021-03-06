#!/usr/bin/env python3

# Prerequisite: pypng (https://github.com/drj11/pypng)

# Issue: Converted images don't work well with \fad

# Test environment: i5-520M, 8GB memory, Radeon 5650M
# Image size: 345 x 164, more than 80% pixels are not fully transparent
# Video: H264 10bit, 1920 x 1080, ~4Mbps
# Software:
# * MPC-HC 1.6.7.7114 (9eb64ec)
# * LAV Filters 0.57.0
# * MadVR 0.86.1
# * xy-vsfilter 3.0.0.211 (git 48eecca)
# Command line for conversion: png-to-ass.py M10_scaled.png --start-time 0:00:10.00 --with-ass-header --text-prefix "{\fad(500,500)}" > PM-M10.ass

# Result: Framerate drops to less than 10fps after beginning time of the image,
#         even after the image has faded in.
#         If \fad is not used, it may stuck for 1 or 2 seconds at the beginning,
#         and plays fine after that
# Note: Tried to manually generate fade-in frames by changing alpha values for
#       each frame. Not useful because the rendering performance was so bad.

import argparse
from datetime import timedelta
import re

import png

ASS_HEADER = """
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def is_same_color(color1, color2):
    assert len(color1) == len(color2) == 4
    if color1[3] == 0:
        # Fully transparent, RGB doesn't matter
        return color2[3] == 0

    return color1 == color2


def from_ass_time(ass_time):
    parts_str = re.match(r"^(\d+):(\d\d):(\d\d)\.(\d\d)$", ass_time).groups()
    parts = [int(x) for x in parts_str]
    return timedelta(
        hours=parts[0],
        minutes=parts[1],
        seconds=parts[2],
        milliseconds=parts[3] * 10,
    )


def to_ass_time(value):
    m, s = divmod(value.seconds, 60)
    h, m = divmod(m, 60)
    h += value.days * 24

    cs = round(value.microseconds / 10000)

    return "{}:{:02d}:{:02d}.{:02d}".format(h, m, s, cs)


def prepare_ass_data(file, pos):
    reader = png.Reader(file)
    width, height, pixels, metadata = reader.asRGBA8()
    org_x, org_y = pos

    for row in range(height):
        raw_pixels = next(pixels)
        assert len(raw_pixels) == width * 4
        blocks = []
        cur_block_start = -1
        block_color = (0, 0, 0, 0)
        origin_column = 0

        for col in range(width):
            pixel_color = tuple(raw_pixels[col*4:col*4+4])
            if is_same_color(pixel_color, block_color):
                continue

            if cur_block_start > -1:
                blocks.append((col - cur_block_start, block_color))
            else:
                origin_column = col

            cur_block_start = col
            block_color = pixel_color

        if block_color[3] != 0:
            blocks.append((col - cur_block_start, block_color))

        if blocks:
            yield (org_x + origin_column, org_y + row), blocks


def build_ass_text(blocks):
    text = ""
    for block_width, block_color in blocks:
        args = list(block_color + (block_width,))
        # Convert regular alpha to ASS alpha (actually transparency)
        args[3] = 0xff - args[3]
        text += (
            r"{{\1c&H{2:02X}{1:02X}{0:02X}\alpha&H{3:X}\p1}}"
            r"m 0 0 l 0 1 {4} 1 {4} 0{{\p0}}"
        ).format(*args)

    return text


def build_lines(file, pos, **kwargs):
    ass_data = prepare_ass_data(file, pos)
    for (row_x, row_y), blocks in ass_data:
        yield build_ass_text(blocks), {"pos": (row_x, row_y)}


def build_arg_parser(parser):
    pass
