import argparse
from datetime import timedelta
import sys
import os
import re

from . import svg, png


ASS_HEADER = """
[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

DIALOGUE_TEMPLATE = (
    r"Dialogue: {layer},{start_time},{end_time},Default,,"
    r"0000,0000,0000,{effect},{text_prefix}{{\an7\bord0\shad0\fnArial\fs20"
    r"\alpha&H0\pos({pos})}}{text}{text_suffix}"
)


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


def vec2(text):
    x, y = [int(v) for v in text.split(",")]
    return x, y


def convert(converter, with_ass_header, **kwargs):
    if with_ass_header:
        res_x, res_y = with_ass_header
        print(ASS_HEADER.strip().format(res_x=res_x, res_y=res_y))

    for line in converter.build_lines(**kwargs):
        if isinstance(line, str):
            text, extra_args = line, {}
        else:
            text, extra_args = line

        line_args = dict(kwargs, **extra_args)
        line_args.update({
            "pos": "{},{}".format(*line_args["pos"]),
            "start_time": to_ass_time(line_args["start_time"]),
            "end_time": to_ass_time(line_args["end_time"]),
            "text": text,
        })
        print(DIALOGUE_TEMPLATE.format(**line_args))


def main():
    parser = argparse.ArgumentParser(prog="siriai")
    parser.add_argument("file")
    parser.add_argument("--layer", type=int, default=0)
    parser.add_argument("--start-time",
                        type=from_ass_time, default="0:00:00.00")
    parser.add_argument("--end-time",
                        type=from_ass_time, default="1:00:00.00")
    parser.add_argument("--pos", type=vec2, default="0,0")
    parser.add_argument("--style", default="Default")
    parser.add_argument("--effect", default="")
    parser.add_argument("--text-prefix", default="")
    parser.add_argument("--text-suffix", default="")
    parser.add_argument("--with-ass-header",
                        type=vec2, nargs="?", const="1920,1080")

    converters = {
        "svg": svg,
        "png": png,
    }
    subparsers = parser.add_subparsers(dest="file_type")
    for file_type, converter in converters.items():
        subparser = subparsers.add_parser(file_type)
        subparser.set_defaults(converter=converter)
        group = parser.add_argument_group(
            "format specific arguments - " + file_type,
        )
        converter.build_arg_parser(group)

    args, remaining = parser.parse_known_args()
    if args.file and not args.file_type:
        _, ext = os.path.splitext(args.file)
        ext = ext.lstrip(".")
        if ext not in converters:
            print("Error: Unknown file type")
            sys.exit(1)

        args.file_type = ext
    
    parser.set_defaults(**vars(args))
    remaining = [args.file, args.file_type] + remaining
    args = parser.parse_args(remaining, namespace=args)

    convert(**vars(args))


if __name__ == '__main__':
    main()
