#!/usr/bin/env python3
"""Build the profile poster in assets/ from the content below.

    pip install fonttools brotli uharfbuzz
    python scripts/build.py

The poster is a cutaway. On top is the city at night. Under the street is its
back end: the systems in production, deeper down the open source workshop,
and at the bottom the earlier jobs as layers of rock, the oldest lowest.

It writes the poster twice, each time cut into seven slices from top to bottom:

    assets/wide-1.svg  .. wide-7.svg    846 px wide, for a desktop screen
    assets/phone-1.svg .. phone-7.svg   360 px wide, shown on screens up to 640 px wide

README.md stacks the seven slices into one picture. They are slices because a
browser redraws a whole image when anything in it moves: this way it redraws
only the slices that move, and only while they are on screen.

The poster has a dark background of its own, so the same files serve both
GitHub themes. Text is drawn as outlines: it looks the same in every browser
and no font has to load.

What is counted, and can be counted in the file:
  * the stars in the sky: one for every test of Almaty Seasons
  * the lit windows in the city: one for every API endpoint of Almaty Seasons
  * the dots in the Dastar hall: one for every request of the race
  * the wires into the first station of a diagram: 18 tools, 5 buyers
Bars are to scale. Everything else is scenery.

Every project has a diagram, and each diagram plays its story again and again:
a request finds its tools, a seat is sold once, a broken stream is finished by
another model, 5,000 requests ask and one wins, then an AI agent books through
the MCP server and is audited. In the city, stars dim and come back, the
tower sends out its rings and cameras flash in the stadium. All of it glides,
and all of it on one shared clock of 24 frames a second (see Motion), so a
browser never redraws the poster more often than that. With "reduce motion"
switched on, nothing moves and every diagram shows its last picture.

To change a number or a sentence, edit CONTENT and run the script again. The
scenery is seeded, so the same content always gives the same picture.
"""
from __future__ import annotations

import io
import math
import random
import re
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
WIDE = 846  # width of a profile README on github.com, in px
PHONE = 360  # width the phone poster is drawn at; GitHub scales it to the screen
GAP = 16  # space between two chambers

# How two slices meet. Stacked images can show a hairline of the page between them when a joint
# does not fall on a whole pixel of the screen. So the README lifts every slice a little higher
# than the slice before it, and each one covers the joint above it. The only tools for that in a
# README are <sub> and <sup>: on GitHub their font is three quarters of their parent's, a
# superscript stands half its font size higher and a subscript a quarter lower, and two levels
# of them are kept (deeper ones are dropped). That gives seven heights, one for each slice.
LADDER = ("sub sub", "sub", "", "sub sup", "sup sub", "sup", "sup sup")  # what the README wraps each slice in


def lift(wrap: str) -> float:
    """How far up GitHub moves what stands in these elements, in font sizes of the README's text."""
    up, size = 0.0, 1.0
    for element in wrap.split():
        size *= .75
        up += size * (.5 if element == "sup" else -.25)
    return up


RAISE = [(lift(below) - lift(above)) * 16 for above, below in zip(LADDER, LADDER[1:])]  # px each slice rides up, at GitHub's largest text
assert min(RAISE) > 1, "a slice no longer rides up over the one before it"
# A wrapped slice is drawn over an unwrapped one. So at most joints the lower slice covers the
# foot of the upper one, but above the unwrapped slice it is the other way round: there the
# upper slice covers the head of the lower one. Whatever gets covered holds nothing but soil.
HEAD = [below == "" for below in LADDER[1:]]
SHADOW = 4  # a chamber's shadow reaches this far under it
SMALLEST = {"wide": 398 / WIDE, "phone": 238 / PHONE}  # the smallest scale GitHub shows each layout at
STRIP = 56  # height of a slice that holds one caption: GitHub gives a line of a README 24 px at least
GRID = 4  # the wide poster is cut on every fourth px: such a joint is whole on screens scaled by quarters

# --------------------------------------------------------------------------
# Content. Every number here should be one you can show the source for.
# In running text, **two stars** set a figure in bold, `backticks` set a
# command, a line break starts a new line, and   is a space that a line
# never breaks at.
# --------------------------------------------------------------------------
CONTENT = {
    "sky": {
        "name": "Zhan Kuatuly",
        "role": "Technical Lead at NDS",
        "body": (
            "I run the backend of the AI assistant for a city of 2 million and lead the team "
            "behind the platform for its sports venues."
        ),
        # Not drawn. It opens the picture's own description, for a reader who cannot see the picture.
        "about": "The picture is a cutaway: Almaty at night on top, the back end under the street.",
        # What is counted in the picture. The sky carries no legend: the Almaty Seasons chamber says
        # what its stars and windows stand for, and so does the picture's own description, in these words.
        "stars": 2553,  # tests of Almaty Seasons
        "windows": 366,  # its API endpoints
        "counted": [
            "stars, one for each test of Almaty Seasons",
            "lit windows, one for each of its API endpoints",
        ],
        # The three buildings with a shaft under them. Each carries only its project's name:
        # what the project is stands in its chamber under the street.
        "tower": "Almaty Seasons",
        "stadium": "DSS",
        "school": "Arlan School",
    },
    # What is written in the ground, from the street down.
    "ground": {
        "open": "Deeper: my own workshop. Open source.",
        "before": "Deeper still: where I worked before NDS. Older is lower.",
    },
    # A project's chamber: what it is, its diagram, one remark under the diagram, three results.
    # In a description, **the bright part** says why the project matters, and a
    # line break is kept on the wide poster only.
    # A result is a figure, what it counts, the fine print, and sometimes an
    # extra: a before/after pair that is drawn as two bars to scale, or a color.
    "production": [
        {
            "title": "Almaty Seasons",
            "desc": "The AI assistant for Almaty residents.\n"
                    "**I\u00a0am its entire backend and infrastructure team.**",
            "figure": "request_path",
            "figure_text": {
                "fan": "18 tools",
                "through": "tools",  # over the lanes, after their number
                "stops": [("intent router", "picks 2 to 4 tools"), ("9B open model", "our own GPU"),
                          ("answer check", "against backend data")],
            },
            "note": "Cutting the tools offered per request from **18** to **2 to 4** fixed tool calling "
                    "in Kazakh. The bottleneck was a prompt of about **11,800** tokens, not model size.",
            "stats": [
                ("366", "API endpoints", "the lit windows in the city above", None),
                ("2,553", "tests", "the stars in the sky above", None),
                ("12 weeks", "to build", "as its only backend engineer", None),
            ],
        },
        {
            "title": "DSS",
            "desc": "One platform for Almaty's municipal sports venues.\n"
                    "**As technical lead, I\u00a0built the money path myself.**",
            "figure": "money_path",
            "figure_text": {
                # The platform's parts, shown as tabs over the diagram, and the one the diagram is about.
                "parts": ["leasing", "events", "tickets", "access control", "analytics"],
                "part": "tickets",
                "fan": "one seat, many buyers",
                "stops": [("seat hold", "no double-sell"), ("order", ""), ("card capture", "two-stage"),
                          ("ticket", "signed QR")],
            },
            "note": "The card acquirer reports a declined payment as HTTP **200** with a false success flag. "
                    "A\u00a0callback that arrives twice is applied once.",
            "stats": [
                ("46 days", "to the first real ticket sale", "counted from the first commit", None),
                ("2.5 min", "CI run time", "cut from **51** minutes", {"before": 3064, "after": 150}),
                ("10", "people", "on the team I lead", None),
            ],
        },
    ],
    "arlan": {
        "title": "Arlan School",
        "desc": "School safety and education quality in one platform for Almaty schools, "
                "**with video and audio analytics.**",
        # Its levels, drawn as stations on one line: a pictogram, a name, what happens there,
        # and small pictograms after the name for what the level takes in.
        "levels_label": "three levels, 10 roles",
        # A line break is where the words break on the wide poster, where they stand centred under
        # their level. The phone poster sets them as running text.
        "levels": [
            ("city", "city and district", "weekly indicators, a map of schools,\nAI\u00a0analytics that leads to tasks for schools", ()),
            ("school", "school", "attendance checked against turnstiles,\nlesson analysis from recordings,\ncameras and safety events",
             ("camera", "sound")),
            ("book", "classroom", "AI\u00a0Teacher, AI\u00a0Tutor,\nAI\u00a0Kitap and a quest room", ()),
        ],
    },
    "opensource": [
        {
            "title": "Switchyard",
            "tag": ("open source", "sun"),  # shown at the top right of the chamber
            "desc": "An LLM gateway in Python.\n**A provider dies mid-answer, "
                    "and another model finishes the same stream.**",
            "figure": "lanes",
            "figure_text": {
                "a": "provider A",
                "b": "provider B",
                "client": "client",
                "cut": "stream cut",
                "done": "finished here",
                "one": "one answer, one stream",
            },
            "note": "Measured against mock providers. Real APIs have had only a smoke test.",
            "stats": [
                ("6,000", "of 6,000 requests completed", "with **30%** of streams cut or stalled", None),
                ("1,306", "broken streams", "all finished on the second model", None),
                ("0.96 ms", "added before the first token", "at p95, at 200 requests a second", None),
            ],
        },
        {
            "title": "Dastar",
            "tag": ("open source", "sun"),  # shown at the top right of the chamber
            "desc": "A reservation engine in TypeScript and Postgres.\n"
                    "**Double booking is refused by the database,**\n**not by application code.**",
            "figure": "field",
            "figure_text": {
                "requests": 5000,  # dots in the field
                "count": "5,000 requests for one table",
                "won": "got it",
                "refused": "refused",
                "run": ("Run the race:", "docker compose run --rm demo"),  # the command, on a plate under the field
            },
            # In place of a remark, a second small diagram: what the engine gives an AI agent.
            # Each stop is a pictogram, a name, and a few quiet words.
            "agents": {
                "agent": "AI agent",
                "stops": [("plug", "MCP server", "4 tools"), ("hourglass", "agents hold", "people confirm"),
                          ("clipboard", "audit", "claims checked")],
            },
            # A result may name a color for its figure: the second one is what happens without the engine.
            "stats": [
                ("4,999", "of 5,000 requests refused", "One gets the table and none overlap.", None),
                ("1,225", "double-booked pairs the usual way", "a plain check-then-insert, with only **50** clients",
                 {"color": "alarm"}),
                ("12", "invariants enforced by Postgres", "with **843** tests, most against a real Postgres 18", None),
            ],
        },
    ],
    # Earlier jobs, newest first. They are drawn as layers of rock, so the last one is the lowest.
    # The last word names the fossil in the layer: pin, car, bridge or train.
    "before": [
        ("SmartTourist", "2025 to 2026", "**First engineer, hired as CTO.** I built the backend from zero "
                                         "through to the company's acquisition by NDS.", "pin"),
        ("Avto-Time", "2024 to 2025", "**Founding engineer** of a car service booking platform. It\u00a0grew to "
                                      "**10,000** monthly users and raised a **$500K** seed.", "car"),
        ("ExploreTest", "2024", "**Co-founder**, in San Francisco. Pitched on stage at CESV 2024 "
                                "and exhibited at TechCrunch Disrupt 2024.", "bridge"),
        ("Crocos", "2023 to 2024", "**Backend engineer** at an agency. I built backends for Almaty Metro "
                                   "and the Astana International Forum.", "train"),
    ],
}

# --------------------------------------------------------------------------
# Colors. Sky blue and sun gold are the colors of the Kazakh flag.
# --------------------------------------------------------------------------
PALETTE = {
    # the chambers under the street, and everything written in them
    "surface": "#121722",
    "edge": "#2d3649",
    "ink": "#e9eef7",
    "quiet": "#9aa3b6",
    "rule": "#273042",
    "idle": "#4b5563",  # refused requests
    "past": "#6e7681",
    "bar": "#6e7781",
    "sky": "#41b8d5",  # work at NDS
    "sun": "#f2c230",  # open source
    "alarm": "#ff7b72",
    # the night above
    "night": ["#050814", "#0a1130", "#182759"],  # top of the sky, middle, horizon
    "glow": "#ff9d5c",  # the city's light on the horizon
    "stars": ["#e6edff", "#b9cfff", "#ffe7c2"],
    "skyink": "#eef2ff",
    "skyquiet": "#a9b4d2",
    "back": ["#8a9bd0", "#41528f", "#26346c"],  # the far range, from the peaks down
    "far": ["#4a5c9c", "#26336a", "#151f49"],  # the range in front of it
    "snow": "#e8eeff",
    "near": ["#0f1739", "#0a1029"],  # the hills in front of them
    "block": ["#0b1027", "#070b1c"],  # buildings: the row behind, the row in front
    "rim": "#32417a",  # edges that catch the light
    "window": ["#ffd071", "#ffe6a8"],
    "lamp": "#ffd98a",
    "beacon": "#ff5d5d",
    "road": "#0d1226",
    # the ground
    "soil": ["#271e18", "#1e1712", "#18120e"],  # under the street, deeper, deepest
    "gravel": "#33281f",  # the bed of the street
    "seam": "#43352a",  # lines in the ground
    "stone": "#3a2e25",
    "well": "#0b1018",  # the stage a diagram stands on
    "welledge": "#1e2636",
    "node": "#161d2a",  # the face of a station
    "soilink": "#b9aea2",
    "shaft": "#0a0d15",
    "layers": ["#1b1410", "#16100d", "#120d0a", "#0e0a08"],  # the rock layers at the bottom
    "fossil": "#6f5a49",
}

# Type sizes in px. The phone poster is scaled down to the screen by about a
# tenth, so its text is drawn a little larger.
TYPE = {
    "wide": SimpleNamespace(
        name=64, role=21.5, role_lead=29, body=15.5, lead=23, title=30, small=13, text=15, text_lead=21.5,
        note=13.5, note_lead=19, figure=26, cap=13, cap_lead=17.5, stop=13, label=12.5, label_lead=16,
        mark=17, mono=13.5),
    "phone": SimpleNamespace(
        name=50, role=20, role_lead=27, body=16.5, lead=24, title=30, small=14, text=16.5, text_lead=24,
        note=14.5, note_lead=21, figure=26, cap=14.5, cap_lead=20, stop=14, label=13, label_lead=16.5,
        mark=17, mono=13.5),
}


# --------------------------------------------------------------------------
# Type: Barlow Condensed for names and titles, Barlow for sentences,
# IBM Plex Mono only for real program output and commands.
# --------------------------------------------------------------------------
class Face:
    def __init__(self, key: str, filename: str) -> None:
        font = TTFont(ROOT / "fonts" / filename)
        font.flavor = None
        raw = io.BytesIO()
        font.save(raw)
        self.key = key
        self.upm: int = font["head"].unitsPerEm
        self._glyphs = font.getGlyphSet()
        self._order = font.getGlyphOrder()
        self._hmtx = font["hmtx"]
        self._hb = hb.Font(hb.Face(raw.getvalue()))
        self._paths: dict[int, str] = {}
        self._shaped: dict[str, tuple[list[tuple[int, int, int]], int]] = {}

    def shape(self, text: str) -> tuple[list[tuple[int, int, int]], int]:
        """Glyph ids with their x and y in font units, and the total advance."""
        if text not in self._shaped:
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(self._hb, buf)
            glyphs, x = [], 0
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
                glyphs.append((info.codepoint, x + pos.x_offset, pos.y_offset))
                x += pos.x_advance
            self._shaped[text] = (glyphs, x)
        return self._shaped[text]

    def path(self, gid: int) -> str:
        """The glyph outline as SVG path data, in font units with y pointing down."""
        if gid not in self._paths:
            pen = SVGPathPen(self._glyphs, ntos=lambda v: f"{v:g}")
            self._glyphs[self._order[gid]].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
            self._paths[gid] = pen.getCommands()
        return self._paths[gid]

    def left_bearing(self, gid: int) -> int:
        return self._hmtx[self._order[gid]][1]


FACES = {
    "d": Face("d", "BarlowCondensed-SemiBold.woff2"),
    "t": Face("t", "Barlow-Regular.woff2"),
    "m": Face("m", "Barlow-Medium.woff2"),
    "b": Face("b", "Barlow-SemiBold.woff2"),
    "c": Face("c", "IBMPlexMono-Regular.woff2"),
}
MONO_SCALE = 0.86  # Plex Mono set next to Barlow at the same size looks large

TOKEN = re.compile(r"(\*\*.+?\*\*|`.+?`)")
Style = tuple[str, str]  # (face key, color)


def num(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def width_of(face: str, text: str, size: float) -> float:
    return FACES[face].shape(text)[1] * size / FACES[face].upm


def plain(markup: str) -> str:
    return re.sub(r"[*`]", "", markup).replace("\u00a0", " ").replace("\n", " ")


class Piece(str):
    """A piece of the drawing that knows which stretch of the poster it lies
    in, from top to bottom. The poster is cut into slices, and a piece goes
    into every slice its stretch reaches."""
    span: tuple[float, float]
    through: bool  # may it run through a joint between two slices? Only the ground may.

    def __new__(cls, text: str, top: float, bottom: float, through: bool = False) -> "Piece":
        piece = super().__new__(cls, text)
        piece.span = (top, bottom)
        piece.through = through
        return piece


class Card:
    """The poster. Layout code draws on it in px from its top left corner. It
    is written out as a stack of slices, each an SVG image of its own, because
    a browser redraws a whole image when anything in it moves: a slice is
    redrawn only for its own motion, and only while it is on screen."""

    def __init__(self, layout: str, title: str, desc: str) -> None:
        self.phone = layout == "phone"
        self.w = PHONE if self.phone else WIDE
        self.h = 0
        self.c = PALETTE
        self.type = TYPE["phone" if self.phone else "wide"]
        self.pad = 14 if self.phone else 22  # margin inside a chamber
        self.inset = 12  # margin inside the stage a diagram stands on
        self.states: set[str] = set()  # the beat states and glows defined so far
        self.phase = 0  # how many beats into its round the diagram being drawn is when the poster loads
        self.title, self.desc = title, desc
        self._glyphs: dict[str, str] = {}
        self.defs: list[str] = []
        self.css: list[str] = []
        self.body: list[str] = []
        self.cuts: list[int] = []  # where one slice ends and the next begins, from the top down
        self.boxes: list[tuple[float, float, float, float]] | None = None  # set to a list to note where text lands

    def add(self, *parts: str) -> None:
        self.body.extend(parts)

    # ---- text ------------------------------------------------------------
    def text(self, x: float, y: float, runs: list[tuple[str, str, str]], size: float,
             anchor: str = "start", optical: bool = False) -> float:
        """Draw one line. runs are (face, color, text). Returns the line's width."""
        sized = [(f, col, s, size * (MONO_SCALE if f == "c" else 1)) for f, col, s in runs if s]
        total = sum(width_of(f, s, sz) for f, _, s, sz in sized)
        if anchor == "end":
            x -= total
        elif anchor == "middle":
            x -= total / 2
        if optical and sized:
            face = FACES[sized[0][0]]
            first = face.shape(sized[0][2])[0][0][0]
            x -= face.left_bearing(first) * sized[0][3] / face.upm
        if self.boxes is not None and sized:
            self.boxes.append((x, y, total, size))
        for f, col, s, sz in sized:
            face = FACES[f]
            glyphs, advance = face.shape(s)
            k = sz / face.upm
            uses = []
            for gid, gx, gy in glyphs:
                d = face.path(gid)
                if not d:
                    continue
                ref = f"{face.key}{gid}"
                self._glyphs[ref] = d
                uses.append(f'<use xlink:href="#{ref}" x="{gx}"' + (f' y="{-gy}"' if gy else "") + "/>")
            if uses:
                self.body.append(
                    f'<g transform="translate({num(x)} {num(y)}) scale({k:.5g})" fill="{col}">{"".join(uses)}</g>'
                )
            x += advance * k
        return total

    def _words(self, markup: str, base: Style, strong: Style, code: Style) -> list[list[tuple[Style, str, bool]]]:
        """Split markup into words. A word is a list of (style, text, space before it)
        that must stay on one line: "**18**." is one word in two styles, and so
        are two words joined by a no-break space."""
        words: list[list[tuple[Style, str, bool]]] = []
        space = tie = False
        for part in TOKEN.split(markup):
            if not part:
                continue
            if part.startswith("`"):
                style, pieces = code, [part[1:-1]]
            elif part.startswith("**"):
                style, pieces = strong, re.findall(r"[^ \t\xa0]+|[ \t\xa0]+", part[2:-2])
            else:
                style, pieces = base, re.findall(r"[^ \t\xa0]+|[ \t\xa0]+", part)
            for piece in pieces:
                if not piece.strip(" \t\xa0"):
                    space, tie = True, "\xa0" in piece
                    continue
                if words and (tie or not space):
                    words[-1].append((style, piece, space))
                else:
                    words.append([(style, piece, space)])
                space = tie = False
        return words

    def para(self, x: float, y: float, markup: str, size: float, width: float, leading: float,
             base: Style | None = None, strong: Style | None = None, code: Style | None = None,
             hang: float = 0.0, balance: bool = True, draw: bool = True, anchor: str = "start") -> float:
        """Draw wrapped text. **bold** and `code` are understood. Lines after the
        first start hang px further right. With balance, a paragraph whose last
        line would be less than half full is set a little narrower, so its
        lines come out about equally long. With anchor "middle" every line is
        centred on x, and the lines are always evened out, since a centred
        paragraph shows both of its edges. With draw off, nothing is drawn and
        the result only tells how far the text would run. Returns the next
        baseline."""
        base = base or ("t", self.c["quiet"])
        strong = strong or ("b", self.c["ink"])
        code = code or ("c", self.c["ink"])

        def w(style: Style, s: str) -> float:
            return width_of(style[0], s, size * (MONO_SCALE if style[0] == "c" else 1))

        def length(word: list[tuple[Style, str, bool]]) -> float:
            return sum(w(st, text) + (w(st, " ") if space and i else 0) for i, (st, text, space) in enumerate(word))

        def wrap(words: list[list[tuple[Style, str, bool]]], limit: float) -> list[list[list[tuple[Style, str, bool]]]]:
            line: list[list[tuple[Style, str, bool]]] = []
            used = 0.0
            lines = [line]
            for word in words:
                gap = w(word[0][0], " ") if (word[0][2] and line) else 0.0
                need = length(word)
                room = limit - (hang if len(lines) > 1 else 0)
                if line and used + gap + need > room:
                    line = []
                    lines.append(line)
                    used, gap = 0.0, 0.0
                line.append(word)
                used += gap + need
            return lines

        for block in markup.split("\n"):
            words = self._words(block, base, strong, code)
            lines = wrap(words, width)
            last = sum(length(word) + (w(word[0][0], " ") if i else 0) for i, word in enumerate(lines[-1]))
            if balance and len(lines) > 1 and (anchor == "middle" or last < 0.5 * (width - hang)):
                low, high = 0.0, width  # the narrowest measure that needs no extra line
                while high - low > 0.5:
                    mid = (low + high) / 2
                    if len(wrap(words, mid)) <= len(lines):
                        high = mid
                    else:
                        low = mid
                lines = wrap(words, high)
            for i, row in enumerate(lines):
                runs: list[tuple[str, str, str]] = []
                for word in row:
                    for j, (style, text, space) in enumerate(word):
                        lead = " " if space and (j or word is not row[0]) else ""
                        if runs and (runs[-1][0], runs[-1][1]) == style:
                            runs[-1] = (style[0], style[1], runs[-1][2] + lead + text)
                        else:
                            if runs and lead:
                                runs[-1] = (runs[-1][0], runs[-1][1], runs[-1][2] + lead)
                            runs.append((style[0], style[1], text))
                if draw:
                    self.text(x + (hang if i else 0), y, runs, size, anchor=anchor)
                y += leading
        return y

    # ---- output ----------------------------------------------------------
    def since(self, start: int, attrs: str) -> None:
        """Put everything drawn since body index start into one group."""
        inner = "".join(self.body[start:])
        del self.body[start:]
        self.body.append(f"<g {attrs}>{inner}</g>")

    def mark(self, start: int, top: float, bottom: float) -> None:
        """Note that everything drawn since body index start lies between top and bottom."""
        self.body[start:] = [Piece(part, top, bottom) for part in self.body[start:]]

    def slices(self) -> list[tuple[int, int]]:
        """Top and bottom of every slice."""
        edges = [0, *self.cuts, self.h]
        assert edges == sorted(set(edges)) and all(isinstance(edge, int) for edge in edges), "cuts out of order or between pixels"
        return list(zip(edges, edges[1:]))

    def render(self, top: int, bottom: int) -> str:
        """One slice as an SVG image: the pieces that reach into it, and of the
        outlines, paints and movements only the ones those pieces use. The slice
        fills its box exactly (preserveAspectRatio none): a browser rounds the
        box to whole pixels, and a low slice that kept its proportions would
        then come out some pixels narrower than its neighbours."""
        assert all(isinstance(part, Piece) for part in self.body), "a piece of the drawing has no place"
        body = "".join(part for part in self.body if part.span[0] < bottom and part.span[1] > top)
        body = f'<g clip-path="url(#pc)">{body}</g>'  # the poster's rounded corners
        defs, found = [], True
        while found:  # a paint may use another one, so look until nothing new turns up
            used = set(re.findall(r'url\(#([^)]+)\)|href="#([^"]+)"', body + "".join(defs)))
            used = {a or b for a, b in used}
            found = [d for d in self.defs if d not in defs and re.search(r'id="([^"]+)"', d).group(1) in used]
            defs += found
        glyphs = "".join(f'<path id="{ref}" d="{d}"/>' for ref, d in self._glyphs.items() if ref in used)
        classes = {name for names in re.findall(r'class="([^"]+)"', body) for name in names.split()}
        css = [rule for rule in self.css if rule.startswith("@") or re.match(r"\.([\w-]+)\{", rule).group(1) in classes]
        style = f"<style>{''.join(css)}</style>" if any(not rule.startswith("@") for rule in css) else ""
        words = (f' role="img" aria-labelledby="t d"><title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
                 if top == 0 else ' aria-hidden="true">')  # the first slice speaks for the whole poster
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.w}" height="{bottom - top}" viewBox="0 {top} {self.w} {bottom - top}" preserveAspectRatio="none"{words}'
            f'<defs>{glyphs}{"".join(defs)}</defs>{style}{body}</svg>\n'
        )


# --------------------------------------------------------------------------
# Parts the chambers share
# --------------------------------------------------------------------------
def chamber(card: Card, at: int, x: float, y: float, w: float, h: float) -> None:
    """Slide a chamber under everything drawn since body index at."""
    c = card.c
    card.body.insert(at, f'<rect x="{num(x)}" y="{num(y + SHADOW)}" width="{num(w)}" height="{num(h)}" rx="13" fill="#000" fill-opacity=".3"/>'
                         f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="{num(h - 1)}" '
                         f'rx="12" fill="{c["surface"]}" stroke="{c["edge"]}"/>')


def tag(card: Card, x: float, y: float, label: str, color: str) -> None:
    """A dot and a few words, ending at x: the tag at the top right of a chamber."""
    c, s = card.c, card.type
    cx = x - card.text(x, y, [("m", c["quiet"], label)], s.small, anchor="end") - 10
    card.add(f'<circle cx="{num(cx)}" cy="{num(y - s.small * 0.33)}" r="4" fill="{c[color]}"/>')


def bars(card: Card, x: float, y: float, width: float, pair: dict) -> None:
    """A before and an after, as two bars to scale."""
    c = card.c
    scale = width / pair["before"]
    card.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(width)}" height="5" rx="1" fill="{c["bar"]}"/>'
             f'<rect x="{num(x)}" y="{num(y + 9)}" width="{num(max(pair["after"] * scale, 2))}" height="5" rx="1" '
             f'fill="{c["sky"]}"/>')


# --------------------------------------------------------------------------
# Motion
# --------------------------------------------------------------------------
# A browser redraws a whole image every time anything in it changes. So
# everything here moves on one clock: FRAMES frames to a beat, and a beat is
# TICK seconds, which makes 24 frames a second. A fade or a glide is written
# as steps of one frame, and the steps of every part fall on the same frames.
# The eye reads that as smooth, and the browser redraws a slice of the poster
# 24 times a second at most, on a screen that could show 60 or 120. Slow
# things, like a star dimming, move on every second frame: it looks the same
# and costs half.
TICK = 0.25  # seconds in a beat; the stories of the diagrams are counted in beats
FRAMES = 6  # frames in a beat
FADE = 5  # frames a part takes to light up or to go dark


def clock(frames: int) -> str:
    """So many frames, as a CSS time."""
    return f"{frames * TICK / FRAMES:.5f}".rstrip("0").rstrip(".") + "s"


def moves(name: str, total: int, stops: list[tuple[int, str, bool]], ahead: int = 0, stride: int = 1) -> str:
    """CSS for a movement that starts again every total frames. A stop is
    (frame, the look at that frame, glides). With glides, the look changes
    into the next stop's, one frame at a time; without, it holds until the
    next stop. ahead is how many frames into the movement the part is when
    the poster loads. With stride 2 the look changes on every second frame."""
    assert total % FRAMES == 0, "a movement lasts a whole number of beats, or it drifts off the clock"
    assert all(frame % stride == 0 for frame, _, _ in stops) and ahead % stride == 0, "off its stride"
    # of two stops on one frame, the later one counts
    stops = [stop for stop, after in zip(stops, stops[1:] + [None]) if after is None or after[0] > stop[0]]
    if stops[0][0] > 0:
        stops.insert(0, (0, stops[0][1], False))
    if stops[-1][0] < total:
        stops.append((total, stops[-1][1], False))
    assert all(a[0] < b[0] for a, b in zip(stops, stops[1:])) and stops[-1][0] == total, "stops out of order"
    rules = ""
    for (frame, look, glides), after in zip(stops, stops[1:] + [None]):
        pace = f";animation-timing-function:steps({(after[0] - frame) // stride})" if glides and after else ""
        rules += f"{100 * frame / total:.4f}".rstrip("0").rstrip(".") + f"%{{{look}{pace}}}"
    start = f" -{clock(ahead)}" if ahead else ""
    return f".{name}{{animation:{name} {num(total * TICK / FRAMES)}s step-end{start} infinite}}@keyframes {name}{{{rules}}}"


# --------------------------------------------------------------------------
# Diagrams. Every project has one, and they share one language:
#
#   a station   a ringed node with a pictogram in it and its name under it
#   a track     the line from one station to the next
#   a state     every part is drawn twice, resting and lit. The lit copy
#               fades in at its beat of the round, or draws itself if it is
#               a line, and stays lit to the end of the round. So the
#               diagram plays its story again and again.
#
# All of it moves on the same clock as the city (see Motion). With "reduce
# motion" switched on, the parts just stay lit: the story's last picture.
# --------------------------------------------------------------------------
ICONS = {  # pictograms in a 16 px box: (lines to stroke, small shapes to fill)
    "funnel": ("M2.5 3.5h11l-4.2 5v4.3l-2.6 1.2v-5.5z", ""),
    "chip": ("M5.4 4.6h5.2a.8.8 0 0 1 .8.8v5.2a.8.8 0 0 1-.8.8H5.4a.8.8 0 0 1-.8-.8V5.4a.8.8 0 0 1 .8-.8z"
             "M6.6 2.2v2.4M9.4 2.2v2.4M6.6 11.4v2.4M9.4 11.4v2.4M2.2 6.6h2.4M2.2 9.4h2.4M11.4 6.6h2.4M11.4 9.4h2.4", ""),
    "shield": ("M8 1.9l5 1.8v3.9c0 2.9-2 5.2-5 6.4-3-1.2-5-3.5-5-6.4V3.7zM5.7 7.8l1.7 1.7 3-3.3", ""),
    "bubble": ("M3.2 3h9.6a1.6 1.6 0 0 1 1.6 1.6v5a1.6 1.6 0 0 1-1.6 1.6H8.4l-3 2.6v-2.6H3.2a1.6 1.6 0 0 1-1.6-1.6v-5A1.6 1.6 0 0 1 3.2 3z",
               "M4.6 6.4h1.5v1.5H4.6zM7.25 6.4h1.5v1.5h-1.5zM9.9 6.4h1.5v1.5H9.9z"),
    "seat": ("M5.6 2.4h4.8a1.5 1.5 0 0 1 1.5 1.5v4.4H4.1V3.9a1.5 1.5 0 0 1 1.5-1.5zM2.7 8.3h10.6v3.1H2.7zM4.4 11.4v2.2M11.6 11.4v2.2", ""),
    "receipt": ("M4 2.3h8v11.4l-2-1.3-2 1.3-2-1.3-2 1.3zM6.3 5.7h3.4M6.3 8.5h3.4", ""),
    "card": ("M2.1 4h11.8a.9.9 0 0 1 .9.9v6.2a.9.9 0 0 1-.9.9H2.1a.9.9 0 0 1-.9-.9V4.9a.9.9 0 0 1 .9-.9zM1.2 6.9h13.6M3.7 9.7h2.6", ""),
    "qr": ("M2.6 2.6h4v4h-4zM9.4 2.6h4v4h-4zM2.6 9.4h4v4h-4z",
           "M4 4h1.2v1.2H4zM10.8 4H12v1.2h-1.2zM4 10.8h1.2V12H4zM9.2 9.2h1.7v1.7H9.2zM11.9 11.9h1.7v1.7h-1.7zM11.9 9.2h1.7v1.2h-1.7zM9.2 12.4h1.2v1.2H9.2z"),
    "screen": ("M2.6 2.9h10.8a.9.9 0 0 1 .9.9v6.6a.9.9 0 0 1-.9.9H2.6a.9.9 0 0 1-.9-.9V3.8a.9.9 0 0 1 .9-.9zM5.6 13.9h4.8M8 11.3v2.6M4.6 5.6l1.9 1.5-1.9 1.5M8.2 8.6h2.6", ""),
    "city": ("M2.4 13.6V7.4h3.3v6.2M5.7 13.6V3.2h4.4v10.4M10.1 13.6V6.2h3.5v7.4M1.3 13.6h13.4M7.2 5.6h1.4M7.2 8h1.4M7.2 10.4h1.4", ""),
    "school": ("M3 13.6V7.3l5-3.1 5 3.1v6.3M1.3 13.6h13.4M6.8 13.6v-3.2h2.4v3.2M8 4.2V1.6h2.5l-.7.9.7.9H8", ""),
    "book": ("M8 4.3C6.5 3.3 4.7 3 2.3 3.1v8.6c2.4-.1 4.2.2 5.7 1.2 1.5-1 3.3-1.3 5.7-1.2V3.1C11.3 3 9.5 3.3 8 4.3zM8 4.3v8.6", ""),
    "camera": ("M2.3 4.7h7.4a1 1 0 0 1 1 1v4.6a1 1 0 0 1-1 1H2.3a1 1 0 0 1-1-1V5.7a1 1 0 0 1 1-1zM10.7 7.1l3.9-2.1v6l-3.9-2.1", ""),
    "sound": ("M2.4 6.6v2.8M5.2 4.6v6.8M8 2.6v10.8M10.8 5v6M13.6 6.8v2.4", ""),
    "robot": ("M4.2 5.6h7.6a1.3 1.3 0 0 1 1.3 1.3v4.6a1.3 1.3 0 0 1-1.3 1.3H4.2a1.3 1.3 0 0 1-1.3-1.3V6.9a1.3 1.3 0 0 1 1.3-1.3z"
              "M8 5.6V3.5M1.5 8.4v2M14.5 8.4v2", "M5.7 8.2h1.5v1.7H5.7zM8.8 8.2h1.5v1.7H8.8zM8 1.6a1 1 0 1 1 0 2a1 1 0 0 1 0-2z"),
    "plug": ("M5.6 1.8v3.4M10.4 1.8v3.4M3.4 5.2h9.2v2.4a4.6 4.6 0 0 1-9.2 0zM8 12.2v2.2", ""),
    "hourglass": ("M4.4 2h7.2M4.4 14h7.2M5.2 2v2.3c0 1.7 2.8 2.4 2.8 3.7 0-1.3 2.8-2 2.8-3.7V2"
                  "M5.2 14v-2.3c0-1.7 2.8-2.4 2.8-3.7 0 1.3 2.8 2 2.8 3.7V14", ""),
    "clipboard": ("M5.4 3.4H4.3a1.1 1.1 0 0 0-1.1 1.1v8.4a1.1 1.1 0 0 0 1.1 1.1h7.4a1.1 1.1 0 0 0 1.1-1.1V4.5a1.1 1.1 0 0 0-1.1-1.1h-1.1"
                  "M5.9 2.2h4.2v2.3H5.9zM5.7 9.4l1.6 1.6 3-3.3", ""),
}


ROUND = 28  # beats in a diagram's round: the story plays, then the finished picture stands until the round ends


def lit(card: Card, start: int, of: int, end: int | None = None, draw: int = 0) -> str:
    """The class for a part that lights up on beat start of a round of so many
    beats and is dark again by beat end, or by the end of the round. It fades
    in and out over a few frames. With draw, the part is a line: instead of
    fading in, it draws itself from its first point over that many beats.
    card.phase says how many beats into its round the diagram is when the
    poster loads, so that neighbours do not all start their stories at the
    same moment."""
    end = of if end is None else end
    name = (f"s{of}_{start}" + ("" if end == of else f"_{end}") + (f"d{draw}" if draw else "")
            + (f"p{card.phase}" if card.phase else ""))
    if name not in card.states:
        card.states.add(name)
        a, z = start * FRAMES, end * FRAMES
        fade = min(FADE, (z - a) // 2)
        if draw:
            hidden, shown, gone = "stroke-dashoffset:1;opacity:1", "stroke-dashoffset:0;opacity:1", "stroke-dashoffset:0;opacity:0"
            stops = [(a, hidden, True), (a + draw * FRAMES, shown, False), (z - fade, shown, True), (z, gone, False)]
        else:
            stops = [(a, "opacity:0", True), (a + fade, "opacity:1", False), (z - fade, "opacity:1", True), (z, "opacity:0", False)]
        card.css.append(moves(name, of * FRAMES, stops, ahead=card.phase * FRAMES))
    return f"st {name}"


def draws(card: Card, start: int, of: int, lasts: int = 1, end: int | None = None) -> str:
    """The attributes of a lit line that draws itself from beat start, in
    lasts beats: its class, and the dash that makes drawing possible."""
    return f'class="{lit(card, start, of, end, draw=lasts)}" pathLength="1" stroke-dasharray="1 2"'


def glow(card: Card, color: str) -> str:
    """The halo round a lit station, in one of the palette's colors. Returns its paint."""
    gid = f"gw{color}"
    if gid not in card.states:
        card.states.add(gid)
        card.defs.append(f'<radialGradient id="{gid}"><stop offset=".45" stop-color="{card.c[color]}" stop-opacity=".34"/>'
                         f'<stop offset="1" stop-color="{card.c[color]}" stop-opacity="0"/></radialGradient>')
    return f"url(#{gid})"


def pictogram(x: float, y: float, icon: str, color: str, scale: float = 1) -> str:
    lines, solids = ICONS[icon]
    at = f'transform="translate({num(x - 8 * scale)} {num(y - 8 * scale)})' + (f' scale({scale})"' if scale != 1 else '"')
    return (f'<path {at} d="{lines}" fill="none" stroke="{color}" stroke-width="1.4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>' + (f'<path {at} d="{solids}" fill="{color}"/>' if solids else ""))


def station(card: Card, x: float, y: float, icon: str, color: str, state: str, r: float = 15, letter: str = "",
            still: bool = True) -> None:
    """A station at rest, and over it the same station lit. With still off, a
    picture that does not move shows it at rest."""
    c = card.c

    def face(ring: str, ink: str) -> None:
        card.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{c["node"]}" stroke="{ring}" stroke-width="1.5"/>')
        if letter:
            card.text(x, y + 4.6, [("b", ink, letter)], 13, anchor="middle")
        else:
            card.add(pictogram(x, y, icon, ink))

    face(c["edge"], c["past"])
    start = len(card.body)
    card.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r + 11)}" fill="{glow(card, color)}"/>')
    face(c[color], c["ink"])
    card.since(start, f'class="{state}"' + ("" if still else ' opacity="0"'))


def track(card: Card, d: str, color: str, start: int, of: int, lasts: int = 1, width: float = 2, rest: bool = True) -> None:
    """A line at rest, and over it the same line lit. The lit line draws
    itself from beat start of the round, in lasts beats."""
    c = card.c
    if rest:
        card.add(f'<path d="{d}" fill="none" stroke="{c["edge"]}" stroke-width="{width}"/>')
    card.add(f'<path {draws(card, start, of, lasts)} d="{d}" fill="none" stroke="{c[color]}" stroke-width="{width}"/>')


def station_label(card: Card, x: float, y: float, name: str, note: str = "", fold: float = 0, size: float = 0) -> None:
    """A station's name and a few quiet words under it, centred on x. With
    fold, words wider than that are set on two lines. size sets the name
    smaller than usual where stations stand close."""
    c, s = card.c, card.type
    card.text(x, y, [("m", c["ink"], name)], size or s.stop, anchor="middle")
    if not note:
        return
    rows = [note]
    if fold and width_of("t", note, s.label) > fold:
        words = note.split(" ")
        cut = min(range(1, len(words)), key=lambda k: max(width_of("t", " ".join(words[:k]), s.label),
                                                         width_of("t", " ".join(words[k:]), s.label)))
        rows = [" ".join(words[:cut]), " ".join(words[cut:])]
    for k, row in enumerate(rows):
        card.text(x, y + s.label_lead * (k + 1), [("t", c["quiet"], row)], s.label, anchor="middle")


def request_path(card: Card, x: float, y: float, w: float, t: dict) -> None:
    """Almaty Seasons. 18 tools reach the router, it lets 2 to 4 of them
    through to the model, and the answer is checked before anybody reads it.
    Three rounds follow each other: with 2 tools, with 3 and with 4."""
    c, s = card.c, card.type
    x, y = round(x), round(y)
    y0, n = y + 47, ROUND
    x1, x2, x3 = (x + 57, x + 150, x + 245) if card.phone else (x + 64, x + 162, x + 266)
    xb = x + w - 11
    card.text(x, y + 10, [("t", c["quiet"], t["fan"])], s.label)

    def wire(j: int) -> str:
        yj, reach = y0 + (j - 8.5) * 2.4, x1 - 15 - x
        return f"M{x} {num(yj)}C{num(x + reach * .55)} {num(yj)} {num(x + reach * .5)} {y0} {x1 - 15} {y0}"

    def lane(off: float) -> str:
        a, b = x1 + 15, x2 - 15
        return (f"M{a} {y0}C{a + 12} {y0} {a + 8} {num(y0 + off)} {a + 20} {num(y0 + off)}H{b - 20}"
                f"C{b - 8} {num(y0 + off)} {b - 12} {y0} {b} {y0}")

    card.add(f'<path d="{"".join(wire(j) for j in range(18))}" fill="none" stroke="{c["past"]}" stroke-width=".9" stroke-opacity=".75"/>'
             f'<path d="{"".join(lane(off) for off in (-7.5, -2.5, 2.5, 7.5))}" fill="none" stroke="{c["edge"]}" stroke-width="1.5"/>')
    # the wires and lanes of each round, and how many tools that makes
    rounds = [((4, 13), (-2.5, 2.5)), ((2, 8, 15), (-7.5, -2.5, 2.5)), ((1, 6, 11, 16), (-7.5, -2.5, 2.5, 7.5))]
    for k, (wires, offs) in enumerate(rounds):
        shown = "" if k == 1 else ' opacity="0"'  # standing still, the picture shows the middle round
        reach = draws(card, k * n + 1, 3 * n, 1, (k + 1) * n)  # the wires reach the router together
        through = draws(card, k * n + 3, 3 * n, 2, (k + 1) * n)  # then the lanes run on to the model
        card.add("".join(f'<path {reach} d="{wire(j)}" fill="none" stroke="{c["sky"]}" stroke-width="1.4"{shown}/>' for j in wires)
                 + "".join(f'<path {through} d="{lane(off)}" fill="none" stroke="{c["sky"]}" stroke-width="1.6"{shown}/>' for off in offs))
        start = len(card.body)
        card.text((x1 + x2) / 2, y0 - 16, [("b", c["ink"], str(len(offs))), ("t", c["quiet"], " " + t["through"])], s.label, anchor="middle")
        card.since(start, f'class="{lit(card, k * n + 3, 3 * n, (k + 1) * n)}"{shown}')
    track(card, f"M{x2 + 15} {y0}H{x3 - 15}", "sky", 7, n, width=3)
    track(card, f"M{x3 + 15} {y0}H{xb - 12}", "sky", 10, n, width=3)
    station(card, x1, y0, "funnel", "sky", lit(card, 2, n))
    station(card, x2, y0, "chip", "sky", lit(card, 5, n))
    station(card, x3, y0, "shield", "sky", lit(card, 8, n))
    card.add(pictogram(xb, y0, "bubble", c["past"]) + f'<g class="{lit(card, 11, n)}">' + pictogram(xb, y0, "bubble", c["ink"]) + "</g>")
    for sx, (name, note) in zip((x1, x2, x3), t["stops"]):
        station_label(card, sx, y0 + 36, name, note, fold=96 if card.phone else 0, size=13.5 if card.phone else 0)


TABS = 28  # room a row of tabs takes at the top of a diagram


def tabs(card: Card, x: float, y: float, w: float, parts: list[str], here: str) -> None:
    """The parts of a platform as a row of tabs across the stage, the way a
    site shows its sections. The part the diagram is about is the open tab.
    y is the baseline of the words."""
    c, s = card.c, card.type
    widths = [width_of("m" if part == here else "t", part, s.label) for part in parts]
    gap = min((w - sum(widths)) / (len(parts) - 1), 24)
    card.add(f'<path d="M{num(x)} {num(y + 9.5)}h{num(w)}" stroke="{c["welledge"]}"/>')
    tx = x
    for part, pw in zip(parts, widths):
        if part == here:
            card.text(tx, y, [("m", c["ink"], part)], s.label)
            card.add(f'<path d="M{num(tx)} {num(y + 9)}h{num(pw)}" stroke="{c["sky"]}" stroke-width="2" stroke-linecap="round"/>')
        else:
            card.text(tx, y, [("t", c["quiet"], part)], s.label)
        tx += pw + gap


def money_path(card: Card, x: float, y: float, w: float, t: dict) -> None:
    """DSS. Over the diagram stand the platform's parts as tabs, with tickets
    open. Many buyers reach for one seat and one of them gets the hold. The
    sale then runs on: order, a card capture in two stages, a signed ticket."""
    c, s = card.c, card.type
    x, y = round(x), round(y)
    if "parts" in t:  # the diagram is one tab of several
        tabs(card, x, y + 10, w, t["parts"], t["part"])
        y += TABS
    y0, n = y + 47, ROUND
    first, last = (x + 58, x + 262) if card.phone else (x + 64, x + 298)
    xs = [first + (last - first) * k / 3 for k in range(4)]
    card.text(x, y + 10, [("t", c["quiet"], t["fan"])], s.label)

    def wire(j: int) -> str:
        yj, reach = y0 + (j - 2) * 7, first - 15 - x
        return f"M{x + 4} {num(yj)}C{num(x + reach * .6)} {num(yj)} {num(x + reach * .5)} {y0} {num(first - 15)} {y0}"

    buyers = "".join(f'<circle cx="{x + 2.5}" cy="{num(y0 + (j - 2) * 7)}" r="2.2"/>' for j in range(5))
    card.add(f'<path d="{"".join(wire(j) for j in range(5))}" fill="none" stroke="{c["past"]}" stroke-width=".9"/>'
             f'<g fill="{c["past"]}">{buyers}</g>'
             # everybody reaches at once; then only the one who got the hold stays lit
             + "".join(f'<path {draws(card, 1, n, 2, 5)} d="{wire(j)}" fill="none" stroke="{c["sky"]}" stroke-width="1.2" opacity="0"/>'
                       for j in (0, 2, 3, 4))
             + f'<path {draws(card, 1, n, 2)} d="{wire(1)}" fill="none" stroke="{c["sky"]}" stroke-width="1.4"/>'
             f'<circle class="{lit(card, 1, n)}" cx="{x + 2.5}" cy="{num(y0 - 7)}" r="2.6" fill="{c["sky"]}"/>')
    for a, b, beat in ((0, 1, 5), (1, 2, 7), (2, 3, 11)):
        track(card, f"M{num(xs[a] + 15)} {y0}H{num(xs[b] - 15)}", "sky", beat, n, width=3)
    station(card, xs[0], y0, "seat", "sky", lit(card, 3, n))
    station(card, xs[1], y0, "receipt", "sky", lit(card, 6, n))
    # the card is captured in two stages: its ring closes one half at a time
    cx, r = xs[2], 15
    card.add(f'<circle cx="{num(cx)}" cy="{y0}" r="{r}" fill="{c["node"]}" stroke="{c["edge"]}" stroke-width="1.5"/>'
             + pictogram(cx, y0, "card", c["past"])
             + f'<g class="{lit(card, 9, n)}"><circle cx="{num(cx)}" cy="{y0}" r="{r + 11}" fill="{glow(card, "sky")}"/>'
             f'<circle cx="{num(cx)}" cy="{y0}" r="{r}" fill="{c["node"]}"/>' + pictogram(cx, y0, "card", c["ink"])
             + f'<path {draws(card, 9, n)} d="M{num(cx)} {y0 - r}a{r} {r} 0 0 1 0 {2 * r}" fill="none" stroke="{c["sky"]}" stroke-width="1.5"/></g>'
             f'<path {draws(card, 8, n)} d="M{num(cx)} {y0 + r}a{r} {r} 0 0 1 0 {-2 * r}" fill="none" stroke="{c["sky"]}" stroke-width="1.5"/>')
    station(card, xs[3], y0, "qr", "sky", lit(card, 12, n))
    card.add(f'<g class="{lit(card, 13, n)}"><circle cx="{num(xs[3] + 11)}" cy="{y0 - 11}" r="5.4" fill="{c["sky"]}" stroke="{c["well"]}" stroke-width="1.5"/>'
             f'<path d="M{num(xs[3] + 8.6)} {y0 - 10.8}l1.7 1.7 2.9-3.1" fill="none" stroke="{c["well"]}" stroke-width="1.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/></g>')
    for sx, (name, note) in zip(xs, t["stops"]):
        station_label(card, sx, y0 + 36, name, note)


def lanes(card: Card, x: float, y: float, w: float, t: dict, room: float = 146) -> None:
    """Switchyard. Provider A sends the answer piece by piece and is cut off.
    The gateway switches to provider B, which sends the remaining pieces, and the client
    reads every piece on one stream. With more room than it needs, the lanes
    stand further apart."""
    c, s = card.c, card.type
    spread = min(max(room - 146, 0), 68)  # more than this and the lanes would fall apart
    x, y = round(x), round(y + (room - 146 - spread) / 2)
    ya = y + 28
    yb = round(ya + 42 + spread * .45)
    yc = round(yb + 52 + spread * .55)
    x0, x1, pitch = x + 36, x + w - 12, 14
    slots = int((x1 - x0 + 5) // pitch)
    sent_a = round(slots * .4)
    sent_b = slots - sent_a - 2  # the switch takes the room of two pieces
    n = sent_a + sent_b + 22  # the finished answer stands for a while before the next round

    def piece(k: int, ly: float, color: str, beat: int) -> str:
        box = f'x="{x0 + k * pitch}" y="{num(ly - 2.5)}" width="9" height="5" rx="1.5"'
        return f'<rect {box} fill="{c["edge"]}"/><rect class="{lit(card, beat, n)}" {box} fill="{c[color]}"/>'

    cut = x0 + sent_a * pitch - 5  # where A's last piece ends
    join = cut + 2 * pitch
    card.add(f'<path d="M{x0 - 6} {ya}H{x1}M{x0 - 6} {yb}H{x1}M{x0 - 6} {yc}H{x1}" stroke="{c["rule"]}"/>')
    for k in range(sent_a):  # A's pieces, and the same pieces as the client reads them
        card.add(piece(k, ya, "sky", 1 + k) + piece(k, yc, "sky", 1 + k))
    beat = sent_a + 1
    card.add(f'<path class="{lit(card, beat, n)}" d="M{cut + 6} {num(ya - 5.5)}l11 11m0 -11l-11 11" stroke="{c["alarm"]}" '
             f'stroke-width="2.2" stroke-linecap="round" fill="none"/>')
    track(card, f"M{cut} {ya}C{cut + 16} {ya} {join - 16} {yb} {join} {yb}", "sun", beat + 1, n)
    for k in range(sent_b):  # B's pieces follow on, and the client reads them with no gap
        card.add(piece(sent_a + 2 + k, yb, "sun", beat + 2 + k) + piece(sent_a + k, yc, "sun", beat + 2 + k))
    done = beat + 2 + sent_b
    end_b, end_c = x0 + slots * pitch + 1, x0 + (sent_a + sent_b) * pitch + 1
    for ex, ly in ((end_b, yb), (end_c, yc)):
        card.add(f'<circle cx="{ex}" cy="{ly}" r="4" fill="{c["edge"]}"/><circle class="{lit(card, done, n)}" cx="{ex}" cy="{ly}" r="4" fill="{c["sun"]}"/>')
    station(card, x + 13, ya, "", "sky", lit(card, 0, n, beat + 1), r=13, letter="A", still=False)  # goes dark once it is cut off
    station(card, x + 13, yb, "", "sun", lit(card, beat + 1, n), r=13, letter="B")
    station(card, x + 13, yc, "screen", "ink", lit(card, 1, n), r=13)
    for ly, key in ((ya, "a"), (yb, "b"), (yc, "client")):
        card.text(x0, ly - 11, [("t", c["quiet"], t[key])], s.label)
    start = len(card.body)
    card.text(cut + 11.5, ya - 12, [("t", c["alarm"], t["cut"])], s.label, anchor="middle")
    card.since(start, f'class="{lit(card, beat, n)}"')
    card.text(x + w, yb + 19, [("t", c["quiet"], t["done"])], s.label, anchor="end")
    card.text(x + w, yc + 19, [("t", c["ink"], t["one"])], s.label, anchor="end")


def field_grid(card: Card, w: float, t: dict) -> tuple[int, int, int, int]:
    """How the dots of the field are laid out: pitch, columns, full rows, dots in the last row."""
    pitch = 4 if card.phone else 3
    cols = int(w // pitch)
    full, rest = divmod(t["requests"], cols)
    return pitch, cols, full, rest


def field(card: Card, x: float, y: float, w: float, t: dict) -> None:
    """Dastar. Every request is one dot, and one of them is gold. The last row
    is short because 5,000 is not a multiple of the row length."""
    c, s = card.c, card.type
    x, y = round(x), round(y)
    left = x  # where words start; the field itself is centred
    pitch, cols, full, rest = field_grid(card, w, t)
    x += (w - cols * pitch) / 2  # centred in its box
    last = y + full * pitch  # top of the short last row
    outline = (f"M{num(x)} {num(y)}H{num(x + cols * pitch)}V{num(last)}H{num(x + rest * pitch)}"
               f"V{num(last + pitch)}H{num(x)}Z")
    n = ROUND
    for pid, color in (("pi", c["idle"]), ("pj", c["bar"])):  # every request at rest, and the moment they all ask
        card.defs.append(
            f'<pattern id="{pid}" x="{num(x)}" y="{num(y)}" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{pitch / 2:g}" cy="{pitch / 2:g}" r="{num(.27 * pitch)}" fill="{color}"/></pattern>')
    card.add(f'<path d="{outline}" fill="url(#pi)"/>'
             f'<path class="{lit(card, 1, n, 3)}" d="{outline}" fill="url(#pj)" opacity="0"/>')
    # the winner, a little right of centre and above the middle. It turns gold once all have asked,
    # and rings run out from it, one on every beat.
    wx = x + (round(cols * .62) + .5) * pitch
    wy = y + (round(full * .42) + .5) * pitch
    rings = ""
    for k, r in enumerate((19, 25, 31)):
        rings += (f'<circle class="{lit(card, 4 + k, n, 6 + k)}" cx="{num(wx)}" cy="{num(wy)}" r="{r}" '
                  f'stroke-opacity="{num(.4 - .1 * k)}" opacity="0"/>')
    card.add(f'<g fill="none" stroke="{c["sun"]}"><g class="{lit(card, 3, n)}">'
             f'<circle cx="{num(wx)}" cy="{num(wy)}" r="7" stroke-opacity=".6"/>'
             f'<circle cx="{num(wx)}" cy="{num(wy)}" r="13" stroke-opacity=".28"/></g>{rings}</g>'
             f'<circle class="{lit(card, 3, n)}" cx="{num(wx)}" cy="{num(wy)}" r="{num(.62 * pitch)}" fill="{c["sun"]}"/>')
    # under the field: the count, and what the two colors mean
    base = last + pitch + 17
    card.text(x, base, [("t", c["quiet"], t["count"])], s.label)
    right = x + cols * pitch
    right -= card.text(right, base, [("t", c["quiet"], t["refused"])], s.label, anchor="end")
    card.add(f'<circle cx="{num(right - 8)}" cy="{num(base - 4.2)}" r="2.3" fill="{c["idle"]}"/>')
    right -= 28
    right -= card.text(right, base, [("t", c["quiet"], t["won"])], s.label, anchor="end")
    card.add(f'<circle cx="{num(right - 8)}" cy="{num(base - 4.2)}" r="2.7" fill="{c["sun"]}"/>')
    if "run" in t:  # the command that runs this race, on a plate
        words, command = t["run"]
        top = base + 12
        if run_fits(card, w, t):
            wide = card.text(left, top + 17.5, [("t", c["quiet"], words)], s.note)
            command_line(card, left + wide + 10, top, command)
        else:  # too narrow for one line: the words stand over the plate
            card.text(left, top + 14, [("t", c["quiet"], words)], s.note)
            command_line(card, left, top + 24, command)


def run_fits(card: Card, w: float, t: dict) -> bool:
    """Whether the words and the command plate under the field fit on one line."""
    words, command = t["run"]
    return width_of("t", words, card.type.note) + 10 + command_width(card, command) <= w


def field_height(card: Card, w: float, t: dict) -> float:
    pitch, _, full, _ = field_grid(card, w, t)
    height = (full + 1) * pitch + 23
    if "run" in t:
        height += 38 if run_fits(card, w, t) else 62
    return height


def agents_height(card: Card) -> float:
    return 84 if card.phone else 68  # on the phone the quiet words take two lines


def agents(card: Card, x: float, y: float, w: float, t: dict) -> None:
    """Dastar, for AI agents. An agent reaches the engine through the MCP
    server. It can hold a table and cannot confirm one, and an audit sets
    what it said against what its calls did. y is the top."""
    c = card.c
    n, first = ROUND, 10  # the story starts once the race over it has been run
    x, y0 = round(x), round(y) + 15
    xs = (x + 25, x + 94, x + 177, x + 256) if card.phone else (x + 24, x + 92, x + 186, x + 281)
    size = 13.5 if card.phone else 0
    # the agent itself has no ring: it is not part of the engine
    card.add(pictogram(xs[0], y0, "robot", c["past"], 1.15) + f'<g class="{lit(card, first, n)}">'
             + pictogram(xs[0], y0, "robot", c["ink"], 1.15) + "</g>")
    for k in range(3):
        track(card, f"M{xs[k] + 13} {y0}H{xs[k + 1] - 13}", "sky", first + 1 + 3 * k, n, width=3)
    station_label(card, xs[0], y0 + 31, t["agent"], size=size)
    for k, (icon, name, words) in enumerate(t["stops"]):
        station(card, xs[k + 1], y0, icon, "sky", lit(card, first + 2 + 3 * k, n), r=13)
        station_label(card, xs[k + 1], y0 + 31, name, words, fold=60 if card.phone else 0, size=size)


# name -> (how to draw it, how tall it is)
PHASES = {"request_path": 0, "money_path": ROUND // 2, "lanes": 0, "field": ROUND // 2}  # beats into its round at the start
FIGURES = {
    "request_path": (request_path, lambda card, w, t: 120 if card.phone else 104),  # on the phone one label takes two lines
    "money_path": (money_path, lambda card, w, t: 104 + (TABS if "parts" in t else 0)),
    "lanes": (lanes, lambda card, w, t: 146),
    "field": (field, field_height),
}
STRETCHES = {"lanes"}  # diagrams that use extra room themselves; the others are centred in it


def levels(card: Card, x: float, y: float, w: float, t: dict) -> float:
    """Arlan School. Its levels are stations on one line, each with a few
    words on what happens there. y is the top; returns the bottom."""
    c, s = card.c, card.type
    n, rows = ROUND, t["levels"]
    card.text(x, y + 10, [("t", c["quiet"], t["levels_label"])], s.label)

    def name_line(tx: float, ty: float, k: int, centred: bool = False) -> None:
        """A level's name, and after it what the level takes in, lit together with
        its station. Centred, tx is the middle of the name and its pictograms together."""
        _, name, _, takes = rows[k]
        if centred:
            tx -= (width_of("m", name, s.stop) + (21.4 + 19 * (len(takes) - 1) if takes else 0)) / 2
        px = tx + card.text(tx, ty, [("m", c["ink"], name)], s.stop) + 15
        for j, icon in enumerate(takes):
            at = (px + 19 * j, ty - 4.5, icon)
            card.add(pictogram(*at, c["past"], .8) + f'<g class="{lit(card, 1 + 4 * k, n)}">' + pictogram(*at, c["sky"], .8) + "</g>")

    if card.phone:  # the line runs down and the words stand to its right
        cy, centres = y + 42, []
        for k, (icon, name, what, takes) in enumerate(rows):
            centres.append(cy)
            name_line(x + 44, cy - 4, k)
            bottom = card.para(x + 44, cy - 4 + s.cap_lead, what.replace("\n", " "), s.cap, w - 44, s.cap_lead) - s.cap_lead
            cy = max(bottom + 34, cy + 46)
        for k in range(len(rows) - 1):
            track(card, f"M{x + 15} {num(centres[k] + 15)}V{num(centres[k + 1] - 15)}", "sky", 3 + 4 * k, n, 2, 3)
        for k, row in enumerate(rows):
            station(card, x + 15, centres[k], row[0], "sky", lit(card, 1 + 4 * k, n))
        return bottom + 5
    y0, col = y + 47, w / len(rows)
    xs = [x + (k + .5) * col for k in range(len(rows))]  # each level stands in the middle of its share of the stage
    for k in range(len(rows) - 1):
        track(card, f"M{num(xs[k] + 15)} {y0}H{num(xs[k + 1] - 15)}", "sky", 3 + 4 * k, n, 2, 3)
    bottoms = []
    for k, (sx, row) in enumerate(zip(xs, rows)):
        station(card, sx, y0, row[0], "sky", lit(card, 1 + 4 * k, n))
        name_line(sx, y0 + 36, k, centred=True)
        bottoms.append(card.para(sx, y0 + 36 + s.cap_lead, row[2], s.cap, col - 8, s.cap_lead, anchor="middle") - s.cap_lead + 5)
    return max(bottoms)


# --------------------------------------------------------------------------
# A project's chamber
# --------------------------------------------------------------------------
def lines_of(card: Card, text: str, size: float, width: float, lead: float) -> float:
    return card.para(0, 0, text, size, width, lead, draw=False) / lead


def told(card: Card, p: dict) -> str:
    """A project's description. The phone poster is narrow, so there it runs on as one paragraph."""
    return p["desc"].replace("\n", " ") if card.phone else p["desc"]


def results(card: Card, x: float, y: float, w: float, stats: list[tuple], draw: bool = True) -> float:
    """Results, one to a row: the figure, then what it counts in bright words
    with the fine print quietly under them. y is the top; returns the bottom."""
    c, s = card.c, card.type
    left = max(width_of("d", figure, s.figure) for figure, *_ in stats) + 18
    gap = 13
    for figure, label, detail, extra in stats:
        pair = extra if extra and "before" in extra else None
        if draw:
            tone = c[extra["color"]] if extra and "color" in extra else c["ink"]
            card.text(x, y + 24, [("d", tone, figure)], s.figure, optical=True)
        end = card.para(x + left, y + 20, label, s.cap, w - left, s.cap_lead, base=("m", c["ink"]), draw=draw) - s.cap_lead
        if detail:
            end = card.para(x + left, end + s.cap_lead, detail, s.cap, w - left, s.cap_lead, draw=draw) - s.cap_lead
        bottom = end + 6
        if pair and card.phone:  # under the words
            if draw:
                bars(card, x + left, bottom + 5, min(w - left, 180), pair)
            bottom += 21
        elif pair and draw:  # at the right end of the row
            bars(card, x + w - 104, y + 16, 104, pair)
        y = max(bottom, y + 30) + gap
    return y - gap


def command_width(card: Card, command: str) -> float:
    return width_of("c", "$ " + command, card.type.mono * MONO_SCALE) + 22


def command_line(card: Card, x: float, y: float, command: str) -> None:
    """A command to copy, on a plate of its own. y is the top of the plate."""
    c, s = card.c, card.type
    card.add(f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(command_width(card, command))}" height="26" rx="6" '
             f'fill="{c["node"]}" stroke="{c["edge"]}"/>')
    card.text(x + 11, y + 17.5, [("c", c["past"], "$ "), ("c", c["ink"], command)], s.mono)


def remark_height(card: Card, p: dict, width: float) -> float:
    """The band under a diagram holds a remark, or for a project with agents
    the small diagram of them. This is how tall its content is, counted as a
    remark is: from its first baseline to its last."""
    s = card.type
    if "agents" in p:
        return agents_height(card) - 10
    return (lines_of(card, p["note"], s.note, width, s.note_lead) - 1) * s.note_lead


def stage(card: Card, x: float, y: float, w: float, h: float) -> str:
    """The darker stage a diagram stands on."""
    c = card.c
    return (f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="{num(h - 1)}" rx="9" '
            f'fill="{c["well"]}" stroke="{c["welledge"]}"/>')


def project_measure(card: Card, w: float, p: dict) -> dict:
    """What decides a chamber's height, so that two chambers next to each other can agree on it."""
    s = card.type
    inner = w - 2 * card.pad
    on_stage = inner - 2 * card.inset
    return {
        "desc": lines_of(card, told(card, p), s.text, inner, s.text_lead),
        "figure": FIGURES[p["figure"]][1](card, on_stage, p["figure_text"]),
        "note": remark_height(card, p, on_stage),
        "results": results(card, 0, 0, inner, p["stats"], draw=False),
    }


def project(card: Card, x: float, y: float, w: float, p: dict, m: dict) -> float:
    """One chamber: its name, what it is, its diagram on a stage with a
    remark under it, and its results. Returns the bottom edge."""
    c, s, pad, inset = card.c, card.type, card.pad, card.inset
    at = len(card.body)
    ix, inner = x + pad, w - 2 * pad
    card.text(ix, y + pad + 25, [("d", c["ink"], p["title"])], s.title, optical=True)
    if "tag" in p:
        tag(card, x + w - pad, y + pad + 18, *p["tag"])
    ty = y + pad + 55
    card.para(ix, ty, told(card, p), s.text, inner, s.text_lead, strong=("t", c["ink"]))
    sy = ty + (m["desc"] - 1) * s.text_lead + 20  # top of the stage
    draw, height = FIGURES[p["figure"]]
    on_stage = inner - 2 * inset
    # Two neighbours have stages of one height. A remark shorter than its neighbour's
    # by a line stands in the middle of its band; by more, the room goes to the diagram.
    slack = m["note"] - remark_height(card, p, on_stage)
    room, shift = (m["figure"] + slack, 0) if slack > s.note_lead + 1 else (m["figure"], slack / 2)
    rule = sy + inset + room + 12  # the hairline between the diagram and the remark
    bottom_of_stage = sy + inset + m["figure"] + 12 + 21 + m["note"] + 13
    card.add(stage(card, ix, sy, inner, bottom_of_stage - sy))
    card.phase = PHASES[p["figure"]]
    if p["figure"] in STRETCHES:
        draw(card, ix + inset, sy + inset, on_stage, p["figure_text"], room)
    else:
        draw(card, ix + inset, sy + inset + (room - height(card, on_stage, p["figure_text"])) / 2, on_stage, p["figure_text"])
    card.phase = 0
    card.add(f'<path d="M{num(ix + inset)} {num(rule + .5)}h{num(on_stage)}" stroke="{c["welledge"]}"/>')
    if "agents" in p:  # its story follows the diagram's, in the same round
        card.phase = PHASES[p["figure"]]
        agents(card, ix + inset, rule + 12 + shift, on_stage, p["agents"])
        card.phase = 0
    else:
        card.para(ix + inset, rule + 21 + shift, p["note"], s.note, on_stage, s.note_lead)
    ry = bottom_of_stage + 12
    results(card, ix, ry, inner, p["stats"])
    bottom = ry + m["results"] + pad - 2
    chamber(card, at, x, y, w, bottom - y)
    return bottom


def slim(card: Card, x: float, y: float, w: float, t: dict) -> float:
    """A chamber for a project told by its parts and not by numbers: its
    name, what it is, and its levels on a stage. Returns the bottom edge."""
    c, s, pad, inset = card.c, card.type, card.pad, card.inset
    at = len(card.body)
    ix, inner = x + pad, w - 2 * pad
    card.text(ix, y + pad + 25, [("d", c["ink"], t["title"])], s.title, optical=True)
    sy = card.para(ix, y + pad + 55, told(card, t), s.text, inner, s.text_lead, strong=("t", c["ink"])) - s.text_lead + 20
    stage_at = len(card.body)
    card.phase = ROUND // 4
    bottom_of_stage = levels(card, ix + inset, sy + inset, inner - 2 * inset, t) + inset - 2
    card.phase = 0
    card.body.insert(stage_at, stage(card, ix, sy, inner, bottom_of_stage - sy))  # the stage goes under its diagram
    bottom = bottom_of_stage + pad
    chamber(card, at, x, y, w, bottom - y)
    return bottom


def port(card: Card, x: float, y: float, quiet: bool) -> None:
    """Where a shaft docks on the top of its chamber: a collar with a light,
    or with a ring where there is no traffic to show."""
    c = card.c
    card.add(f'<rect x="{num(x - 11)}" y="{num(y - 4)}" width="22" height="8" rx="3" fill="{c["shaft"]}" stroke="{c["rim"]}"/>'
             + (f'<circle cx="{num(x)}" cy="{num(y)}" r="1.9" fill="none" stroke="{c["sky"]}" stroke-width="1.1"/>' if quiet
                else f'<circle cx="{num(x)}" cy="{num(y)}" r="1.9" fill="{c["sky"]}"/>'))


# --------------------------------------------------------------------------
# Scenery
# --------------------------------------------------------------------------
# How often things in the city happen. Everything moves on the poster's one
# clock (see Motion), so each of these is a whole number of beats.
TWINKLE = (4, 4.75, 5.5, 6.25, 7, 8, 9.25, 10.5)  # seconds from one dimming of a star to the next
FLASH = (5, 6.25, 7.5, 8.75, 5.75, 9.5, 7, 10.25)  # seconds between two flashes of one camera


def every(seconds: float) -> int:
    """So many seconds in frames. It has to be a whole number of beats."""
    assert (seconds / TICK).is_integer(), "off the beat"
    return round(seconds / TICK) * FRAMES


class Noise:
    """Smooth random values along a line, the same for the same seed."""

    def __init__(self, seed: int, wavelength: float) -> None:
        rng = random.Random(seed)
        self.wavelength = wavelength
        self.values = [rng.uniform(-1, 1) for _ in range(512)]

    def __call__(self, x: float) -> float:
        t = x / self.wavelength
        i = math.floor(t)
        f = (1 - math.cos((t - i) * math.pi)) / 2
        return self.values[i % 512] * (1 - f) + self.values[(i + 1) % 512] * f


def gradient(card: Card, gid: str, kind: str, coords: tuple, stops: list[tuple]) -> None:
    """A gradient in px. kind is "linear" (x1, y1, x2, y2) or "radial" (cx, cy, r).
    stops are (offset, color, opacity)."""
    marks = "".join(f'<stop offset="{o}" stop-color="{col}" stop-opacity="{op}"/>' for o, col, op in stops)
    if kind == "linear":
        x1, y1, x2, y2 = (num(v) for v in coords)
        card.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" '
                         f'x2="{x2}" y2="{y2}">{marks}</linearGradient>')
    else:
        cx, cy, r = (num(v) for v in coords)
        card.defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" '
                         f'r="{r}">{marks}</radialGradient>')


def outline(points: list[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{num(x)} {num(y)}" for x, y in points)


# What is left of each earlier job, pressed into its layer of rock. Each drawing fits a box 62 wide and 30 high.
FOSSILS = {
    # a pin on a map, at the end of a dotted route (SmartTourist, travel)
    "pin": ('<path d="M2 26c9 -12 18 6 27 -3s8 -9 13 -9" stroke-dasharray=".1 4.6"/>'
            '<path d="M50 3a7 7 0 0 1 7 7c0 6 -7 13 -7 13s-7 -7 -7 -13a7 7 0 0 1 7 -7z"/><circle cx="50" cy="10" r="2.2"/>'),
    # a car (Avto-Time, car service)
    "car": ('<path d="M4 23v-6.5q0 -2 2 -2.3l7 -1.2l6 -7.4q1 -1.2 3 -1.2h13q2 0 3 1.2l6 7.4l8 1.4q2 .4 2 2.4v6.2h-6M44 23h-24M12 23h-8"/>'
            '<circle cx="16" cy="23" r="4.2"/><circle cx="48" cy="23" r="4.2"/><path d="M21 12.5h19"/>'),
    # a suspension bridge (ExploreTest, San Francisco)
    "bridge": ('<path d="M0 22h62M17 28v-26M45 28v-26M17 9h0M0 15q9 0 17 -12q14 22 28 0q8 12 17 12"/>'
               '<path d="M6 14.6v7M11 11.6v10M24 12.6v9M31 14v8M38 12.6v9M51 11.6v10M56 14.6v7" stroke-width=".9"/>'),
    # a metro train on its track (Crocos, Almaty Metro)
    "train": ('<path d="M0 27h62M6 22v-12q0 -3 3 -3h17v15zM29 22v-15h20q7 2 8 10v5zM9 22v2.5M22 22v2.5M33 22v2.5M53 22v2.5"/>'
              '<path d="M10 11h4.5v4.5h-4.5zM18 11h4.5v4.5h-4.5zM32.5 11h4.5v4.5h-4.5zM40.5 11h4.5v4.5h-4.5zM49 11.5q3 1.2 3.6 4h-3.6z" stroke-width=".9"/>'),
}


def fossil(card: Card, kind: str, x: float, y: float) -> None:
    card.add(f'<g transform="translate({num(x)} {num(y)})" fill="none" stroke="{card.c["fossil"]}" stroke-width="1.4" '
             f'stroke-linecap="round" stroke-linejoin="round">{FOSSILS[kind]}</g>')


def starfield(card: Card, count: int, top: float, ceiling, boxes: list[tuple], seed: int) -> str:
    """Exactly count stars above the line ceiling(x). No star sits behind a box
    (x, y, w, h) or on top of another star, so every one of them can be counted."""
    c, W = card.c, card.w
    rng = random.Random(seed)
    # a brighter band across the sky, like the Milky Way
    ax, ay, bx, by = W * .12, top - 60, W * 1.08, ceiling(W * .9) - 20
    length = math.hypot(bx - ax, by - ay)
    cells: dict[tuple[int, int], list[tuple[float, float, float]]] = {}
    kinds = [(.5, (.34, .48, .62), 72), (.75, (.62, .8), 22), (1.05, (.92,), 5), (1.45, (1,), 1)]
    weights = [k[2] for k in kinds]
    buckets: dict[tuple[float, float, str], list[str]] = {}
    twinkle: list[str] = []
    placed = 0
    while placed < count:
        x, y = rng.uniform(3, W - 3), rng.uniform(top, ceiling(0) + 80)
        limit = ceiling(x) - 4
        if y > limit:
            continue
        depth = (y - top) / max(limit - top, 1)
        off = abs((bx - ax) * (ay - y) - (ax - x) * (by - ay)) / length
        if rng.random() > (.28 + .72 * math.exp(-(off / (W * .09 + 46)) ** 2)) * (1 - .6 * depth ** 2.6):
            continue
        r, opacities, _ = rng.choices(kinds, weights)[0]
        if any(bx0 - r - 7 < x < bx0 + bw + r + 7 and by0 - r - 3 < y < by0 + bh + r + 3 for bx0, by0, bw, bh in boxes):
            continue
        key = (int(x // 4), int(y // 4))
        near = [p for dx in (-1, 0, 1) for dy in (-1, 0, 1) for p in cells.get((key[0] + dx, key[1] + dy), [])]
        if any(math.hypot(x - px, y - py) < r + pr + 1.1 for px, py, pr in near):
            continue
        cells.setdefault(key, []).append((x, y, r))
        placed += 1
        color = rng.choices(c["stars"], (70, 18, 12))[0]
        if r > 1.2 or (r > 1 and rng.random() < .45) or (r > .7 and rng.random() < .04):  # the ones that twinkle
            kind = int(rng.random() * len(TWINKLE))
            start = TICK * int(rng.random() * TWINKLE[kind] / TICK)  # how far into its round it is at the start
            twinkle.append(f'<circle class="tw t{kind}" cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{color}" '
                           f'style="animation-delay:-{num(start)}s"/>')
        else:
            buckets.setdefault((r, rng.choice(opacities), color), []).append(f"M{num(x)} {num(y)}h0")
    still = "".join(f'<path d="{"".join(d)}" stroke="{color}" stroke-width="{2 * r:g}" stroke-linecap="round" '
                    f'stroke-opacity="{opacity}" fill="none"/>' for (r, opacity, color), d in sorted(buckets.items()))
    return f'<g id="stars">{still}{"".join(twinkle)}</g>'


def scene(card: Card, margin: float) -> dict:
    """The city at night, from the top of the sky down to the street. Returns
    where the ground starts and where the three buildings with a shaft stand."""
    c, s, W = card.c, card.type, card.w
    t = CONTENT["sky"]
    rng = random.Random(11)
    wide = not card.phone

    # ---- the words come first, because the stars keep clear of them
    words_at = len(card.body)
    card.boxes = []
    if wide:
        card.text(margin, 78, [("d", c["skyink"], t["name"])], s.name, optical=True)
        card.text(margin, 118, [("m", c["skyink"], t["role"])], s.role)
        text_bottom = card.para(margin, 150, t["body"], s.body, 462, s.lead, base=("t", c["skyquiet"])) - s.lead
    else:
        card.text(margin, 60, [("d", c["skyink"], t["name"])], s.name, optical=True)
        y = card.para(margin, 96, t["role"], s.role, W - 2 * margin, s.role_lead, base=("m", c["skyink"]))
        text_bottom = card.para(margin, y + 6, t["body"], s.body, W - 2 * margin, s.lead, base=("t", c["skyquiet"])) - s.lead
    far_base = round(text_bottom + (150 if wide else 206))  # foot of the mountains
    near_base = far_base + 46  # foot of the hills
    street = near_base + 60
    tower_x, school_x, stadium_x = (150, W / 2, 640) if wide else (62, W / 2, 292)

    # ---- mountains: one far range with snow, one row of hills in front
    n1, n2, n3, n4 = Noise(21, 150 if wide else 110), Noise(22, 52), Noise(23, 17), Noise(24, 90)

    def far(x: float) -> float:
        lift = .5 + .5 * math.exp(-((x - W * .6) / (W * .3)) ** 2)  # the range is highest right of the middle
        return far_base - 8 - lift * (46 * (1 - abs(n1(x))) ** 1.5 + 13 * (1 - abs(n2(x))) + 3.5 * n3(x))

    b1, b2, b3 = Noise(41, 124 if wide else 92), Noise(42, 43), Noise(43, 14)

    def back(x: float) -> float:
        lift = .42 + .58 * math.exp(-((x - W * .72) / (W * .36)) ** 2)
        return far_base - 30 - lift * (70 * (1 - abs(b1(x))) ** 1.9 + 24 * (1 - abs(b2(x))) ** 1.3 + 5 * b3(x))

    def skyline(x: float) -> float:
        return min(back(x), far(x))

    def near(x: float) -> float:
        hill = 24 * math.exp(-((x - tower_x) / 34) ** 2)  # the tower stands on a hill of its own
        return near_base - 8 - 9 * (1 + n4(x)) - 3 * n2(x + 300) - hill

    xs = [i * 2 for i in range(int(W // 2) + 2)]

    # ---- the sky
    gradient(card, "sk", "linear", (0, 0, 0, street),
             [(0, c["night"][0], 1), (.55, c["night"][1], 1), (1, c["night"][2], 1)])
    gradient(card, "hg", "radial", (W * .55, far_base + 30, W * .62), [(0, c["glow"], .2), (1, c["glow"], 0)])
    # The sky runs on under the road, and the road a pixel under the ground: where two flat shapes only
    # touch, a screen whose pixels fall between them lets the page behind the picture shine through.
    card.body.insert(words_at, f'<rect width="{W}" height="{num(street + 14)}" fill="url(#sk)"/>'
                               f'<rect width="{W}" height="{num(street)}" fill="url(#hg)"/>')
    words_at += 1

    # the moon: a thin crescent
    mx, my = (W - 78, 62) if wide else (W - 44, 38)
    card.defs.append(f'<mask id="mn"><rect x="{mx - 20}" y="{my - 20}" width="40" height="40" fill="#fff"/>'
                     f'<circle cx="{mx + 6}" cy="{my - 4}" r="12"/></mask>')
    gradient(card, "mg", "radial", (mx, my, 34), [(0, c["snow"], .16), (1, c["snow"], 0)])
    moon = (f'<circle cx="{mx}" cy="{my}" r="34" fill="url(#mg)"/>'
            f'<circle cx="{mx}" cy="{my}" r="13" fill="{c["snow"]}" mask="url(#mn)"/>')

    # ---- landmarks' names, so that the stars keep clear of them too
    tower_base = near(tower_x) + 2
    tower_top = tower_base - 102
    marks_at = len(card.body)

    def mark(x: float, y: float, name: str, anchor: str) -> None:
        card.text(x, y, [("d", c["skyink"], name)], s.mark, anchor=anchor, optical=anchor == "start")

    # the tower's name stands beside it; the other two stand over their buildings, on one line
    if wide:
        mark(tower_x + 20, tower_base - 46, t["tower"], "start")
        mark(school_x, street - 76, t["school"], "middle")
        mark(stadium_x, street - 76, t["stadium"], "middle")
    else:
        mark(tower_x + 46, tower_top - 14, t["tower"], "start")
        mark(school_x, street - 112, t["school"], "middle")
        mark(stadium_x, street - 112, t["stadium"], "middle")
    boxes = [(x, y - size * .82, w, size * 1.08) for x, y, w, size in card.boxes]
    card.boxes = None
    boxes += [(mx - 15, my - 15, 30, 30), (tower_x - 9, tower_top - 4, 18, 104)]
    card.body.insert(words_at, starfield(card, t["stars"], 7, skyline, boxes, seed=5) + moon)
    marks_at += 1

    scenery: list[str] = []
    # a shooting star, now and then
    (sx, sy), (tx, ty), tail = ((W - 150, 12), (-184, 60), (-44, 14.4)) if wide else ((W - 26, text_bottom + 14), (-140, 38), (-36, 9.8))
    scenery.append(f'<g transform="translate({num(sx)} {num(sy)})"><path class="ss" d="M0 0l{num(tail[0])} {num(tail[1])}" '
                   f'stroke="{c["snow"]}" stroke-width="1.2" stroke-linecap="round" opacity="0" style="animation-delay:-18.5s"/></g>')
    for gid, line, colors, snow_from, snow_alpha in (("bm", back, c["back"], 24, .78), ("fm", far, c["far"], 9, .5)):
        peak = min(line(x) for x in xs)
        gradient(card, gid, "linear", (0, peak, 0, far_base + 40), [(0, colors[0], 1), (.34, colors[1], 1), (1, colors[2], 1)])
        scenery.append(f'<path d="{outline([(0, street)] + [(x, line(x)) for x in xs] + [(W, street)])}Z" fill="url(#{gid})"/>')
        snowline = [peak + snow_from + 5 * n3(x * 1.7 + 90) + 4 * n2(x + 40) for x in xs]
        run: list[int] = []
        for i, x in enumerate(xs + [None]):  # snow wherever the range rises above its snowline
            if x is not None and line(x) < snowline[i]:
                run.append(i)
            elif run:
                if len(run) > 5:
                    top_edge = [(xs[j], line(xs[j])) for j in run]
                    low_edge = [(xs[j], snowline[j] + 4 * n3(xs[j] * 2.3 + 500) + 2.5 * math.sin(j * .9)) for j in reversed(run)]
                    scenery.append(f'<path d="{outline(top_edge + low_edge)}Z" fill="{c["snow"]}" fill-opacity="{snow_alpha}"/>')
                run = []
    gradient(card, "nh", "linear", (0, near_base - 40, 0, street), [(0, c["near"][0], 1), (1, c["near"][1], 1)])
    scenery.append(f'<path d="{outline([(0, street)] + [(x, near(x)) for x in xs] + [(W, street)])}Z" fill="url(#nh)"/>')

    # ---- the tower on its hill: a mast with a pod, a red light, and the rings
    x, base, top, pod = tower_x, tower_base, tower_top, tower_base - 58
    gradient(card, "bg", "radial", (x, top, 9), [(0, c["beacon"], .55), (1, c["beacon"], 0)])
    scenery.append(
        f'<path d="M{x - 4.6} {num(base)}L{x - 1.9} {num(pod)}h3.8L{x + 4.6} {num(base)}Z" fill="{c["block"][1]}" '
        f'stroke="{c["rim"]}" stroke-width=".9"/>'
        f'<path d="M{x} {num(pod - 14)}V{num(top)}" stroke="{c["rim"]}" stroke-width="1.5"/>'
        f'<rect x="{x - 4.4}" y="{num(pod - 14)}" width="8.8" height="5" rx="1.6" fill="{c["block"][1]}" stroke="{c["rim"]}" stroke-width=".9"/>'
        f'<rect x="{x - 6.6}" y="{num(pod - 9)}" width="13.2" height="9" rx="2.6" fill="{c["block"][1]}" stroke="{c["rim"]}" stroke-width=".9"/>'
        f'<path d="M{x - 4.4} {num(pod - 4.5)}h8.8" stroke="{c["window"][0]}" stroke-width="1.3" stroke-dasharray="1.5 1.15"/>'
        f'<circle cx="{x}" cy="{num(top)}" r="9" fill="url(#bg)"/>'
        f'<circle class="bk" cx="{x}" cy="{num(top)}" r="1.7" fill="{c["beacon"]}"/>')
    for i in range(6):  # the signal it sends out: each ring is two arcs, left and right of the mast
        r = 9 + 6 * i
        dx, dy = r * math.cos(math.radians(46)), r * math.sin(math.radians(46))
        scenery.append(
            f'<path class="rg" d="M{num(x + dx)} {num(top - dy)}A{r} {r} 0 0 1 {num(x + dx)} {num(top + dy)}'
            f'M{num(x - dx)} {num(top - dy)}A{r} {r} 0 0 0 {num(x - dx)} {num(top + dy)}" fill="none" stroke="{c["sky"]}" '
            f'stroke-width="1.3" stroke-linecap="round" stroke-opacity="{num(.95 - .09 * i)}" '
            f'style="animation-delay:{num(TICK * i - 3)}s"/>')

    # ---- the city: a skyline, a lower row in front of it where nothing else stands, and exactly as many
    # lit windows as there are endpoints. A window is only lit where nothing stands in front of it.
    def clear(x0: float, x1: float) -> bool:
        return all(not (x0 < cx + half and x1 > cx - half) for cx, half in ((school_x, 50), (stadium_x, 66)))

    masts = [stadium_x + dx for dx in (-54, -32, 32, 54)]
    cover = [(school_x - 41, street - 25, 82, 25), (school_x - 13, street - 39, 26, 39), (school_x - 1, street - 56, 13, 19),
             (school_x + 11, street - 30, 33, 30), (stadium_x - 51, street - 21, 102, 21)]
    cover += [(mx_ - 4, street - 52, 8, 52) for mx_ in masts] + boxes  # no lit window behind any words either
    cover += [(lx - 3, street - 14, 6, 14) for lx in range(24, int(W), 66)]
    ww, wh, px, py = (2.4, 3.2, 5, 6) if wide else (2.2, 3, 4.5, 5.5)
    slots: list[tuple[float, float, int]] = []
    front: list[tuple[float, float, float, float]] = []
    rows = []
    for row, (lo, hi) in enumerate(((30, 66), (14, 44)) if wide else ((52, 96),)):  # the skyline, then the row in front
        x, blocks = -6 - 9 * row, []
        while x < W + 4:
            bw = rng.choice((11, 13, 16, 16, 21, 21, 26, 31))
            bh = rng.uniform(lo, hi) * (.5 if abs(x + bw / 2 - tower_x) < 44 else 1)
            if row == 0 or clear(x, x + bw):
                blocks.append(f"M{num(x)} {num(street)}v-{num(bh)}h{bw}v{num(bh)}z")
                if row == 1:
                    front.append((x, street - bh, bw, bh))
                wx = x + 2.6
                while wx < x + bw - ww - 1.6:
                    wy = street - bh + 4
                    while wy < street - wh - 4:
                        slots.append((round(wx, 1), round(wy, 1), row))
                        wy += py
                    wx += px
            x += bw + rng.choice((0, 0, 1, 2, 3))
        rows.append(f'<path d="{"".join(blocks)}" fill="{c["block"][row]}"/>')
    open_slots = [(wx, wy) for wx, wy, row in slots
                  if 1 <= wx <= W - ww - 1 and not any(
                      wx < cx + cw + 1 and wx + ww > cx - 1 and wy < cy + ch + 1 and wy + wh > cy - 1
                      for cx, cy, cw, ch in cover + (front if row == 0 else []))]
    rng.shuffle(open_slots)
    lit: list[tuple[float, float]] = []
    for wx, wy in open_slots:  # a lit window never touches another lit window
        if len(lit) == t["windows"]:
            break
        if all(abs(wx - lx_) >= ww + .8 or abs(wy - ly_) >= wh + .8 for lx_, ly_ in lit):
            lit.append((wx, wy))
    assert len(lit) == t["windows"], f"room for only {len(lit)} lit windows"
    scenery += rows
    cut = round(len(lit) * .72)
    for color, take in zip(c["window"], (lit[:cut], lit[cut:])):
        scenery.append(f'<path class="wn" d="{"".join(f"M{num(wx)} {num(wy)}h{ww}v{wh}h-{ww}z" for wx, wy in take)}" fill="{color}"/>')

    # ---- the school: low, with a flag and a lit door
    x, y = school_x, street
    wall, line = "#131c44", "#6b7fc4"
    scenery.append(
        f'<path d="M{x - 40} {y}v-24h80v24z" fill="{wall}" stroke="{line}" stroke-width=".9"/>'
        f'<path d="M{x - 12} {y}v-31l12 -7l12 7v31z" fill="{wall}" stroke="{line}" stroke-width=".9"/>'
        f'<path d="M{x - 3.5} {y}v-10h7v10z" fill="{c["sky"]}"/>'
        f'<path d="{"".join(f"M{x + dx} {y - 18}h4.4v5h-4.4zM{x + dx} {y - 9.5}h4.4v5h-4.4z" for dx in (-35.5, -28, -20.5, 16.5, 24, 31.5))}" fill="{line}" fill-opacity=".5"/>'
        f'<path d="M{x} {y - 38}v-16" stroke="{c["skyquiet"]}" stroke-width="1"/>'
        f'<path d="M{x + .5} {y - 54}h10v6.5h-10z" fill="{c["sky"]}"/><circle cx="{x + 5.5}" cy="{y - 50.7}" r="1.5" fill="{c["sun"]}"/>')

    # ---- the stadium: a lit bowl with four masts
    x, y = stadium_x, street - 8
    gradient(card, "sg", "radial", (x, y - 4, 70), [(0, "#d8f4ff", .34), (.5, "#d8f4ff", .1), (1, "#d8f4ff", 0)])
    gradient(card, "pg", "radial", (x, y, 40), [(0, "#7ff0c8", 1), (1, "#2f9e86", 1)])
    mast_lines = "".join(
        f'<path d="M{x + dx} {y + 4}V{num(y - 40)}" stroke="{c["rim"]}" stroke-width="1.2"/>'
        f'<path d="M{x + dx - 3} {num(y - 40)}h6" stroke="{c["snow"]}" stroke-width="2.2" stroke-linecap="round"/>'
        f'<path d="M{x + dx} {num(y - 40)}L{x + dx * .1 - 16} {y}h32z" fill="#d8f4ff" fill-opacity=".07"/>'
        for dx in (-54, -32, 32, 54))
    flashes = ""
    for j, (angle, period) in enumerate(zip((205, 238, 268, 300, 332, 18, 158, 96), FLASH)):  # cameras in the stands
        fx, fy = x + 43 * math.cos(math.radians(angle)), y + 8.8 * math.sin(math.radians(angle))
        flashes += (f'<g class="fl f{j}" opacity="0" style="animation-delay:-{num(TICK * rng.randrange(int(period / TICK)))}s">'
                    f'<path d="M{num(fx - 2.4)} {num(fy)}h4.8M{num(fx)} {num(fy - 2.4)}v4.8" stroke="#fff" stroke-width=".8" stroke-linecap="round"/>'
                    f'<circle cx="{num(fx)}" cy="{num(fy)}" r="1" fill="#fff"/></g>')
    scenery.append(
        f'<ellipse cx="{x}" cy="{y - 12}" rx="70" ry="40" fill="url(#sg)"/>{mast_lines}'
        f'<ellipse cx="{x}" cy="{y}" rx="50" ry="11.5" fill="{c["block"][1]}" stroke="{c["rim"]}"/>'
        f'<ellipse cx="{x}" cy="{y - 1}" rx="35" ry="6" fill="url(#pg)"/>'
        f'<path d="M{x - 35} {y - 1}h70M{x} {y - 7}v12" stroke="#eafff7" stroke-width=".6" stroke-opacity=".7"/>{flashes}')

    # ---- the street, its lamps, and a few cars
    gradient(card, "lg", "radial", (0, 0, 9), [(0, c["lamp"], .5), (1, c["lamp"], 0)])
    lamps = "".join(f'<g transform="translate({lx} {num(street - 11)})"><circle r="9" fill="url(#lg)"/>'
                    f'<path d="M0 0v11" stroke="{c["rim"]}" stroke-width="1"/><circle r="1.5" fill="{c["lamp"]}"/></g>'
                    for lx in range(24, int(W), 66) if clear(lx - 4, lx + 4))
    cars = "".join(  # a car is two lights: white in front, red behind
        f'<circle cx="{num(W * at + (-5 if back else 5))}" cy="{num(street + (10 if back else 4.5))}" r="1.5" fill="#fff6dc"/>'
        f'<circle cx="{num(W * at + (5 if back else -5))}" cy="{num(street + (10 if back else 4.5))}" r="1.3" fill="{c["beacon"]}"/>'
        for at, back in (((.11, False), (.37, True), (.58, False), (.87, True)) if wide else ((.14, False), (.5, True), (.84, False))))
    scenery.append(
        f'<rect y="{num(street)}" width="{W}" height="15" fill="{c["road"]}"/>'
        f'<path d="M0 {num(street + .5)}H{W}" stroke="{c["rim"]}"/>'
        f'<path d="M0 {num(street + 7.2)}H{W}" stroke="{c["rim"]}" stroke-width=".8" stroke-dasharray="9 13" stroke-opacity=".8"/>'
        f'{lamps}{cars}')

    card.body.insert(marks_at, "".join(scenery))
    # a star dims and comes back, more slowly than it went
    # Everything in the city is slow, so it moves on every second frame. Only the shooting star is fast.
    card.css += [moves(f"t{k}", every(period), [(0, "opacity:1", True), (10, "opacity:.22", True), (28, "opacity:1", False)], stride=2)
                 for k, period in enumerate(TWINKLE)]
    # a camera flashes and the flash dies away
    card.css += [moves(f"f{j}", every(period), [(0, "opacity:1", True), (8, "opacity:0", False)], stride=2)
                 for j, period in enumerate(FLASH)]
    fly = 18  # frames the shooting star takes
    card.css += [
        # a ring swells bright and fades, one beat after the ring inside it, so a wave runs outwards
        moves("rg", every(3), [(0, "opacity:.5", True), (4, "opacity:1", True), (20, "opacity:.5", False)], stride=2),
        # the red light breathes
        moves("bk", every(2), [(0, "opacity:1", True), (16, "opacity:.2", True), (34, "opacity:1", False)], stride=2),
        # the shooting star: nothing for most of 24 seconds, then it flies and fades
        moves("ss", every(24), [(every(24) - fly - 2, "opacity:0;transform:translate(0,0)", True),
                                (every(24) - fly + 2, f"opacity:.9;transform:translate({num(tx * 4 / fly)}px,{num(ty * 4 / fly)}px)", True),
                                (every(24) - 2, f"opacity:0;transform:translate({tx}px,{ty}px)", False)]),
    ]
    card.mark(0, 0, street + 14)  # all of it lies above the ground
    return {"ground": street + 14, "tower": tower_x, "school": school_x, "stadium": stadium_x}


# --------------------------------------------------------------------------
# The poster: the city, and the ground under it
# --------------------------------------------------------------------------
def poster(layout: str) -> Card:
    sky, ground = CONTENT["sky"], CONTENT["ground"]
    production, opensource, before = CONTENT["production"], CONTENT["opensource"], CONTENT["before"]
    arlan = CONTENT["arlan"]

    def spoken(p: dict) -> str:
        parts = [f'{p["title"]}{", " + p["tag"][0] if "tag" in p else ""}.', plain(p["desc"])]
        if "parts" in p["figure_text"]:
            names = p["figure_text"]["parts"]
            parts.append(f'Its parts: {", ".join(names[:-1])} and {names[-1]}. The diagram shows {p["figure_text"]["part"]}.')
        parts.append(plain(p.get("note", "")))
        if "run" in p["figure_text"]:
            parts.append(" ".join(p["figure_text"]["run"]) + ".")
        if "agents" in p:
            parts.append(f'For an {p["agents"]["agent"]}: ' + "; ".join(f"{name}, {words}" for _, name, words in p["agents"]["stops"]) + ".")
        counted = [f"{figure} {plain(label)}{', ' + plain(detail) if detail else ''}".rstrip(".") + "."
                   for figure, label, detail, _ in p["stats"]]
        return " ".join(part for part in parts + counted if part)

    card = Card(layout, sky["name"],
                f'{sky["role"]}. {plain(sky["body"])} {sky["about"]} In the picture: {sky["stars"]:,} {sky["counted"][0]}; '
                f'{sky["windows"]} {sky["counted"][1]}. Under the street: '
                + " ".join(spoken(p) for p in production) + f' {arlan["title"]}. {plain(arlan["desc"])} '
                + f'{arlan["levels_label"].capitalize()}: ' + "; ".join(f"{name}: {plain(what)}" for _, name, what, _ in arlan["levels"])
                + f'. {ground["open"]} '
                + " ".join(spoken(p) for p in opensource) + f' {ground["before"]} '
                + " ".join(f"{name}, {years}: {plain(text)}" for name, years, text, _ in before))
    c, s, W = card.c, card.type, card.w
    T = 16 if card.phone else 22  # left edge of the text that stands free
    M = 8 if card.phone else 22  # left edge of the chambers
    place = scene(card, T)
    ground_y = place["ground"]
    under_at = len(card.body)  # the ground itself is slid in here once its height is known
    shafts: list[tuple[float, float, bool]] = []  # x, bottom, and whether it is quiet: no traffic to show yet

    captions: list[tuple[float, float]] = []  # top and bottom of each text that stands in the soil

    def caption(y: float, text: str) -> float:
        """Words that stand in the soil and mark a new depth: an arrow down and
        the words. Where there is room, a dotted line runs on to the right edge."""
        start = len(card.body)
        card.add(f'<path d="M{T + 1} {num(y - 8)}l4.5 5 4.5-5" fill="none" stroke="{c["soilink"]}" stroke-width="1.6" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
        end = card.para(T + 20, y, text, s.text, W - 2 * T - 20, s.text_lead, base=("m", c["ink"]))
        reach, right = T + 20 + width_of("m", text, s.text) + 14, W - T
        if end - s.text_lead == y and reach < right - 40:  # the words take one line and leave room
            card.add(f'<path d="M{num(reach)} {num(y - 4.5)}H{num(right)}" stroke="{c["seam"]}" stroke-dasharray="2 4"/>')
        captions.append((y - s.text - 5, end - s.text_lead + 8))
        card.mark(start, *captions[-1])
        return end

    def room(top: float, draw) -> int:
        """Draw a chamber with its top at top, note where it lies, and return its bottom edge."""
        start = len(card.body)
        bottom = round(draw())
        card.mark(start, top, bottom + SHADOW)
        return bottom

    def in_caption(y: float, reach: float) -> bool:
        return any(top - reach < y < bottom + reach for top, bottom in captions)

    def lap(joint: int) -> float:
        """How far one slice may reach over the other at joint number joint, in px of the poster."""
        return RAISE[joint] / SMALLEST[layout]

    def near_joint(y: float, reach: float) -> bool:
        return any(at - reach < y < at + lap(k) + reach if HEAD[k] else at - lap(k) - reach < y < at + reach
                   for k, at in enumerate(card.cuts))

    def cut(y: float, down: bool = False) -> int:
        """Cut the poster at y, or at the nearest place above it (down: below it) that the layout allows."""
        step = 1 if card.phone else GRID
        at = int(-(-y // step) * step if down else y // step * step)
        card.cuts.append(at)
        return at

    def cut_above(top: float) -> int:
        """Cut the poster above a chamber whose top edge is at top. The collar of its shaft stands
        5 px higher. Where the slice above covers the head of this one, the head is soil."""
        joint = len(card.cuts)
        return cut(top - 5 - (lap(joint) if HEAD[joint] else 1))

    def strip(floor: float, text: str) -> int:
        """A caption in a slice of its own, under a chamber whose bottom edge is at floor. Returns the slice's bottom."""
        assert not HEAD[len(card.cuts)], "this joint would cover the caption"
        top = cut(floor + SHADOW + lap(len(card.cuts)) + 1, down=True)
        end = caption(top + 34, text)
        assert end - s.text_lead == top + 34, "the caption no longer fits on one line"
        return cut(top + STRIP)

    y = round(ground_y + 60)  # top of the first chambers; the shafts run down to here

    # The poster is cut into seven slices, the same number in both layouts, because the README
    # pairs them. Every cut runs through the soil between two chambers, and whatever one slice
    # covers of the other there is soil (see LADDER).
    #   wide:   city | Almaty Seasons and DSS | Arlan School | a caption | Switchyard and Dastar | a caption | earlier jobs
    #   phone:  city | Almaty Seasons | DSS | Arlan School | Switchyard | Dastar | earlier jobs
    if card.phone:
        w = W - 2 * M
        for p, spot in zip(production, ("tower", "stadium")):
            shafts.append((place[spot], y, False))
            cut_above(y)
            y = room(y, lambda: project(card, M, y, w, p, project_measure(card, w, p))) + GAP
        shafts.append((place["school"], y, True))
        cut_above(y)
        y = room(y, lambda: slim(card, M, y, w, arlan))
        y = round(caption(y + 38, ground["open"]) - s.text_lead + 22)
        for p in opensource:
            cut_above(y)
            y = room(y, lambda: project(card, M, y, w, p, project_measure(card, w, p))) + GAP
        y = round(caption(y - GAP + 40, ground["before"]) - s.text_lead + 24)
        cut(y - 8)
    else:
        w = (W - 2 * M - GAP) / 2
        for specs, spots in ((production, ("tower", "stadium")), (opensource, None)):
            measures = [project_measure(card, w, p) for p in specs]
            shared = {key: max(m[key] for m in measures) for key in measures[0]}  # both chambers keep the same rows
            if spots:
                shafts += [(place[spot], y, False) for spot in spots]
                cut_above(y)
            y = room(y, lambda: max(project(card, M + i * (w + GAP), y, w, p, shared) for i, p in enumerate(specs)))
            if spots:
                top = y + GAP + 8
                shafts.append((place["school"], top, True))
                cut_above(top)
                y = strip(room(top, lambda: slim(card, M, top, W - 2 * M, arlan)), ground["open"]) + 6
        y = strip(y, ground["before"]) + 8

    # ---- the earlier jobs, as layers of rock: the older, the lower
    wave = Noise(31, 120)
    layers: list[str] = []
    tops = []
    rock_at = len(card.body)
    for k, (name, years, text, kind) in enumerate(before):
        tops.append(y)
        card.text(T, y + 34, [("d", c["ink"], name)], 22, optical=True)
        card.text(T, y + 52, [("t", c["soilink"], years)], s.small)
        fossil(card, kind, W - T - 62, y + 20)
        if card.phone:
            y = card.para(T, y + 52 + s.note_lead + 6, text, s.note, W - 2 * T, s.note_lead, base=("t", c["soilink"]),
                          strong=("m", c["ink"])) - s.note_lead + 20
        else:
            bottom = card.para(T + 190, y + 33, text, s.note, W - 2 * T - 190 - 96, s.note_lead, base=("t", c["soilink"]),
                               strong=("m", c["ink"])) - s.note_lead
            y = max(bottom, y + 52) + 20
    H = round(y + 18)
    card.mark(rock_at, tops[0], H)
    for k, top in enumerate(tops):  # each layer runs from its wavy top edge to the bottom of the poster
        edge = [(x, top + 3.5 * wave(x + 400 * k) + 2 * math.sin(x / 37 + k)) for x in range(0, int(W) + 9, 8)]
        layers.append(Piece(f'<path d="{outline(edge + [(W, H), (0, H)])}Z" fill="{c["layers"][min(k, len(c["layers"]) - 1)]}"/>'
                            f'<path d="{outline(edge)}" fill="none" stroke="{c["seam"]}" stroke-width="1.2"/>', top - 7, H))

    # ---- the ground: soil, seams and stones, then the shafts from the street down to the chambers
    rng = random.Random(3)
    gradient(card, "so", "linear", (0, ground_y, 0, tops[0]),
             [(0, c["soil"][0], 1), (.45, c["soil"][1], 1), (1, c["soil"][2], 1)])
    under = [Piece(f'<rect y="{num(ground_y)}" width="{W}" height="{num(H - ground_y)}" fill="url(#so)"/>', ground_y, H, through=True),
             Piece(f'<rect y="{num(ground_y)}" width="{W}" height="7" fill="{c["gravel"]}"/>'
                   f'<path d="M0 {num(ground_y + 3.5)}H{W}" stroke="{c["stone"]}" stroke-width="3" stroke-dasharray="2 5" stroke-linecap="round"/>',
                   ground_y, ground_y + 7)]
    depth = ground_y + 40
    while depth < tops[0] - 30:  # seams: thin wavy lines across the soil
        seam = Noise(rng.randrange(999), rng.choice((90, 140, 200)))
        line = (f'<path d="{outline([(x, depth + 7 * seam(x)) for x in range(0, int(W) + 9, 8)])}" fill="none" '
                f'stroke="{c["seam"]}" stroke-opacity="{num(rng.uniform(.35, .8))}"/>')
        if not in_caption(depth, 8) and not near_joint(depth, 9):
            under.append(Piece(line, depth - 8, depth + 8))
        depth += rng.uniform(46, 110)
    stones: dict[int, str] = {}  # in bands of 100 px, so that a slice carries only the stones near it
    for sx, sy, rx in ((rng.uniform(0, W), rng.uniform(ground_y + 12, tops[0] - 8), rng.choice((1, 1.3, 1.6, 2.2, 3.4)))
                       for _ in range(int((tops[0] - ground_y) * W / 2600))):
        if not in_caption(sy, 3) and not near_joint(sy, 3):
            stones[int(sy // 100)] = stones.get(int(sy // 100), "") + (
                f"M{num(sx)} {num(sy)}a{num(rx)} {num(rx * .62)} 0 1 0 {num(2 * rx)} 0a{num(rx)} {num(rx * .62)} 0 1 0 {num(-2 * rx)} 0z")
    under += [Piece(f'<path d="{d}" fill="{c["stone"]}"/>', 100 * band - 3, 100 * band + 103, through=True)
              for band, d in sorted(stones.items())]
    under += layers
    for k, (x, bottom, quiet) in enumerate(shafts):
        top = ground_y
        under.append(Piece(
            f'<path d="M{num(x - 5)} {num(top)}V{num(bottom)}M{num(x + 5)} {num(top)}V{num(bottom)}" stroke="{c["edge"]}"/>'
            f'<rect x="{num(x - 4.5)}" y="{num(top)}" width="9" height="{num(bottom - top)}" fill="{c["shaft"]}"/>'
            f'<path d="M{num(x - 3)} {num(top + 6)}V{num(bottom)}" stroke="{c["rule"]}" stroke-width="6" stroke-dasharray="1 7"/>'
            f'<path d="M{num(x - 8)} {num(top)}h16" stroke="{c["rim"]}" stroke-width="2"/>', top - 1, bottom, through=True))
        if quiet:  # no traffic to show here: a ring
            under.append(Piece(f'<circle cx="{num(x)}" cy="{num(top + 14)}" r="2.6" fill="none" stroke="{c["sky"]}" stroke-width="1.3"/>',
                               top + 10, top + 18))
        else:  # in use: a light glides down and starts again at the street. It stays inside the city's slice.
            gradient(card, f"eg{k}", "radial", (x, top + 9, 8), [(0, c["sky"], .6), (1, c["sky"], 0)])
            under.append(Piece(
                f'<g class="el" style="animation-delay:-{num(TICK * 4 * k)}s"><circle cx="{num(x)}" cy="{num(top + 9)}" r="8" fill="url(#eg{k})"/>'
                f'<circle cx="{num(x)}" cy="{num(top + 9)}" r="2.4" fill="{c["sky"]}"/></g>', top, top + 38))
    card.body[under_at:under_at] = under
    for x, bottom, quiet in shafts:
        start = len(card.body)
        port(card, x, bottom, quiet)
        card.mark(start, bottom - 5, bottom + 5)
    # The part of a shaft above the first chamber is 60 px long, and the poster is cut some 52 px down it.
    # The light comes up out of the dark at the street, glides down for two seconds and goes out well
    # before the cut, above the foot of the slice that the next slice covers.
    card.css.append(moves("el", every(2), [(0, "opacity:0;transform:translateY(0)", True), (6, "opacity:1;transform:translateY(3px)", True),
                                           (34, "opacity:1;transform:translateY(17px)", True), (42, "opacity:0;transform:translateY(21px)", False)],
                          stride=2))

    # the whole poster has rounded corners; each slice is clipped by the same shape
    card.defs.append(f'<clipPath id="pc"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    card.css.append("@media (prefers-reduced-motion:reduce){.tw,.fl,.rg,.bk,.ss,.el,.st{animation:none}}")
    card.h = H
    return card


MOVING = re.compile(r'class="(?:tw|fl|rg|bk|ss|el|st)[ "]')  # the classes of everything that moves


def main() -> None:
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.svg"):
        old.unlink()
    for layout in ("wide", "phone"):
        card = poster(layout)
        slices = card.slices()
        assert len(slices) == len(RAISE) + 1, "the README pairs seven slices"
        assert min(bottom - top for top, bottom in slices) >= STRIP, "a slice is lower than a line of the README can be"
        for part in card.body:  # a moving piece in two slices would have both redrawn for it
            homes = [k for k, (top, bottom) in enumerate(slices, 1) if part.span[0] < bottom and part.span[1] > top]
            assert len(homes) == 1 or not MOVING.search(part), f"a moving piece lies across slices {homes}"
            for k, at in enumerate(card.cuts):  # where one slice covers the other, only ground may lie
                reach = RAISE[k] / SMALLEST[layout]
                clear = (part.span[1] <= at or part.span[0] >= at + reach) if HEAD[k] else (part.span[0] >= at or part.span[1] <= at - reach)
                assert part.through or clear, (
                    f"joint {k + 1} at {at}: something from {num(part.span[0])} to {num(part.span[1])} lies where a slice covers the other")
        sizes = []
        for k, (top, bottom) in enumerate(slices, 1):
            path = out / f"{layout}-{k}.svg"
            path.write_text(card.render(top, bottom), encoding="utf-8")
            sizes.append(path.stat().st_size)
        heights = " + ".join(str(bottom - top) for top, bottom in slices)
        print(f"assets/{layout}-1.svg to {layout}-{len(slices)}.svg  {card.w} x {card.h} ({heights})  {sum(sizes) / 1024:.0f} KB")
    # The joints only close if README.md wraps the seven pictures the way LADDER says.
    rows = [row.strip() for row in (ROOT / "README.md").read_text(encoding="utf-8").split("</p>")[0].split("<p>")[1].strip().splitlines()]
    wraps = [("".join(f"<{e}>" for e in wrap.split()), "".join(f"</{e}>" for e in reversed(wrap.split()))) for wrap in LADDER]
    if len(rows) != len(LADDER) or not all(row.startswith(a + "<picture>") and row.endswith("</picture>" + b) for row, (a, b) in zip(rows, wraps)):
        print("README.md no longer wraps the seven pictures the way LADDER says: the slices will not close up")


if __name__ == "__main__":
    main()
