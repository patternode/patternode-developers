"""Draws the architecture diagrams as SVG. Python 3.10+, standard library only.

    python website/diagrams/architecture.py          # writes website/docs/architecture/img/*.svg
    python website/diagrams/architecture.py --check  # fails if a committed SVG differs

Edit this file, never the SVGs. Colours are the brand roles in website/src/css/tokens.css:
the partner's side is indigo (secondary), Patternode is cyan (primary) on navy, the
partner's client is amber, and asynchronous events are dashed amber.
"""

from __future__ import annotations

import sys
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "img"
FONT = "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, 'SF Mono', Consolas, monospace"

INK, MUTED, FAINT = "#1b202c", "#525c74", "#9ba6c0"
NAVY, CYAN = "#1b202c", "#00b8e6"
ZONES = {  # fill, stroke, label
    "client": ("#fff8eb", "#c98a00", "#8a5a00"),
    "partner": ("#f4f6ff", "#4f46e5", "#352da5"),
    "pn": ("#ecf9ff", "#007fa0", "#004e64"),
    "neutral": ("#f7f8fb", "#c6cddc", "#525c74"),
    "ot": ("#fff3f6", "#ca2464", "#84003c"),
}
BOXES = {  # fill, stroke, title, sub
    "plain": ("#ffffff", "#c6cddc", INK, MUTED),
    "partner": ("#ffffff", "#7077ff", INK, MUTED),
    "client": ("#ffffff", "#e69f00", INK, MUTED),
    "pn": (NAVY, CYAN, "#ffffff", "#afe4f9"),
    "pnlight": ("#ffffff", "#0099c0", INK, MUTED),
    "planned": ("#ffffff", "#9ba6c0", MUTED, FAINT),
    "ot": ("#ffffff", "#e8457c", INK, MUTED),
}
ARROWS = {  # colour, dashed
    "request": ("#4f46e5", False),
    "response": ("#007fa0", False),
    "event": ("#c27c00", True),
    "internal": ("#525c74", False),
    "oneway": ("#ca2464", False),
    "faint": ("#9ba6c0", True),
}


def width_of(s: str, size: float) -> float:
    return len(s) * size * 0.56


class Diagram:
    def __init__(self, name: str, w: int, h: int, title: str, subtitle: str, desc: str):
        self.name, self.w, self.h = name, w, h
        self.title, self.subtitle, self.desc = title, subtitle, desc
        self.body: list[str] = []
        self.labels: list[str] = []  # drawn last, above the arrows

    # Primitives ---------------------------------------------------------------------

    def text(self, x, y, s, size=13, weight=400, fill=INK, anchor="start", mono=False, italic=False):
        style = ' font-style="italic"' if italic else ""
        family = MONO if mono else FONT
        self.body.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
                         f'fill="{fill}" text-anchor="{anchor}"{style}>{escape(s)}</text>')

    def zone(self, x, y, w, h, label, kind="neutral", sub=None, dashed=False):
        fill, stroke, colour = ZONES[kind]
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="1.5"{dash}/>')
        self.text(x + 16, y + 26, label.upper(), 12, 600, colour)
        if sub:
            self.text(x + 16, y + 44, sub, 12, 400, MUTED)

    def box(self, x, y, w, h, title, lines=(), kind="plain", tag=None, mono_lines=False):
        fill, stroke, tcol, scol = BOXES[kind]
        dash = ' stroke-dasharray="5 4"' if kind == "planned" else ""
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="1.6"{dash}/>')
        n = 1 + len(lines)
        top = y + h / 2 - (n - 1) * 9 + 5
        self.text(x + w / 2, top, title, 14.5, 600, tcol, "middle")
        for i, line in enumerate(lines):
            self.text(x + w / 2, top + 19 + i * 17, line, 12, 400, scol, "middle", mono=mono_lines)
        if tag:
            self.chip(x + w - 10, y - 9, tag, kind="planned" if kind == "planned" else "tag", anchor="end")

    def chip(self, x, y, s, kind="tag", anchor="start"):
        colours = {"tag": ("#e8ecff", "#352da5"), "planned": ("#eef0f5", MUTED), "pn": ("#d5f2fe", "#004e64"),
                   "event": ("#fff1d6", "#8a5a00"), "ok": ("#dcf5ec", "#00694d")}
        bg, fg = colours[kind]
        w = width_of(s, 11) + 16
        x0 = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
        self.labels.append(f'<rect x="{x0:.1f}" y="{y}" width="{w:.1f}" height="19" rx="9.5" fill="{bg}"/>'
                           f'<text x="{x0 + w / 2:.1f}" y="{y + 13.5}" font-family="{FONT}" font-size="11" '
                           f'font-weight="600" fill="{fg}" text-anchor="middle">{escape(s)}</text>')

    def arrow(self, pts, label=None, kind="request", at=0.5, both=False, label_dy=0, label_lines=None):
        colour, dashed = ARROWS[kind]
        d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        start = f' marker-start="url(#tail-{kind})"' if both else ""
        self.body.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="2"{dash}'
                         f' marker-end="url(#head-{kind})"{start}/>')
        lines = label_lines or ([label] if label else [])
        if lines:
            # The label sits at fraction `at` along the longest segment.
            segs = list(zip(pts, pts[1:]))
            (x1, y1), (x2, y2) = max(segs, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
            cx, cy = x1 + (x2 - x1) * at, y1 + (y2 - y1) * at + label_dy
            w = max(width_of(s, 11.5) for s in lines) + 14
            h = 8 + 15 * len(lines)
            self.labels.append(f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="5" '
                               f'fill="#ffffff" stroke="{colour}" stroke-width="0.8" opacity="0.97"/>')
            for i, s in enumerate(lines):
                self.labels.append(f'<text x="{cx:.1f}" y="{cy - h / 2 + 16 + i * 15:.1f}" font-family="{FONT}" '
                                   f'font-size="11.5" fill="{colour}" font-weight="500" text-anchor="middle">'
                                   f'{escape(s)}</text>')

    def person(self, x, y, label, colour="#4f46e5"):
        self.body.append(f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{colour}" stroke-width="2"/>'
                         f'<path d="M {x - 15} {y + 28} Q {x} {y + 6} {x + 15} {y + 28}" fill="none" '
                         f'stroke="{colour}" stroke-width="2"/>')
        self.text(x, y + 46, label, 12, 500, MUTED, "middle")

    def note(self, x, y, lines, size=12.5, fill=MUTED, gap=19, weight=400):
        for i, s in enumerate(lines):
            self.text(x, y + i * gap, s, size, weight, fill)

    def legend(self, y, items):
        x = 40
        for kind, label in items:
            colour, dashed = ARROWS[kind]
            dash = ' stroke-dasharray="6 5"' if dashed else ""
            self.body.append(f'<path d="M {x} {y} L {x + 34} {y}" stroke="{colour}" stroke-width="2"{dash} '
                             f'marker-end="url(#head-{kind})"/>')
            self.text(x + 44, y + 4, label, 12, 400, MUTED)
            x += 44 + width_of(label, 12) + 34

    # Output -------------------------------------------------------------------------

    def svg(self) -> str:
        defs = []
        for kind, (colour, _) in ARROWS.items():
            defs.append(f'<marker id="head-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                        f'markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" '
                        f'fill="{colour}"/></marker>')
            defs.append(f'<marker id="tail-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                        f'markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" '
                        f'fill="{colour}"/></marker>')
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
            f'height="{self.h}" role="img" aria-labelledby="t-{self.name} d-{self.name}">',
            f'<title id="t-{self.name}">{escape(self.title)}</title>',
            f'<desc id="d-{self.name}">{escape(self.desc)}</desc>',
            "<!-- Generated by website/diagrams/architecture.py. Edit the script, not this file. -->",
            "<defs>" + "".join(defs) + "</defs>",
            f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="16" fill="#ffffff" stroke="#e1e5ee"/>',
            f'<rect x="0" y="0" width="{self.w}" height="6" rx="3" fill="{NAVY}"/>',
            f'<rect x="0" y="0" width="140" height="6" rx="3" fill="{CYAN}"/>',
        ]
        self.text(40, 46, self.title, 21, 600, INK)
        self.text(40, 70, self.subtitle, 13.5, 400, MUTED)
        # The title was appended last; move it to the front so it sits under everything else.
        title_els = self.body[-2:]
        self.body = title_els + self.body[:-2]
        return "\n".join(head + self.body + self.labels + ["</svg>", ""])


# The diagrams ---------------------------------------------------------------------------


def system_context() -> Diagram:
    d = Diagram("context", 1240, 720, "Patternode from the outside",
                "Three parties. Your systems call Patternode; Patternode keeps nothing and never calls into your network.",
                "Your client's sources feed your ingest workload, which sends bars under opaque series names to the "
                "Patternode API and stores the segments it gets back in your own store. Patternode sends signed "
                "events to your event receiver. Your application draws from your store for your users.")
    d.zone(30, 100, 250, 470, "Your client", "client", "a utility, a fund, a fleet")
    d.box(55, 175, 200, 82, "Assets and markets", ["sensors, meters,", "instruments"], "client")
    d.box(55, 315, 200, 82, "Sources", ["historian, SCADA,", "meters, market feeds"], "client")
    d.arrow([(155, 257), (155, 315)], kind="internal")

    d.zone(310, 100, 490, 470, "You, the partner", "partner", "your cloud, your brand, your data")
    d.box(330, 175, 200, 82, "Key vault", ["keys, webhook secret"], "partner")
    d.box(330, 315, 200, 82, "Segment store", ["segments and edges,", "per client prefix"], "partner")
    d.box(330, 455, 200, 82, "Your application", ["galleries, tiles, alerts"], "partner")
    d.box(580, 175, 200, 82, "Ingest workload", ["builds bars, calls the API"], "partner")
    d.box(580, 315, 200, 82, "Event receiver", ["verifies, dedupes, queues"], "partner")
    d.box(580, 455, 200, 82, "Observability", ["SLIs, traces, alerts"], "partner")
    d.arrow([(255, 356), (295, 356), (295, 160), (680, 160), (680, 175)], "readings", "internal", at=0.25)
    d.arrow([(530, 216), (580, 216)], kind="faint")
    d.arrow([(580, 240), (555, 240), (555, 335), (530, 335)], kind="internal")
    d.arrow([(580, 372), (530, 372)], kind="internal")
    d.arrow([(430, 397), (430, 455)], kind="internal")

    d.zone(950, 100, 260, 470, "Patternode", "pn", "your jurisdiction: ANZ, EU or US")
    d.box(970, 175, 220, 110, "Patternode API", ["{anz,eu,us}.api.patternode.com", "REST · gRPC · events"], "pn")
    d.box(970, 330, 220, 64, "Delve", ["shards at every level"], "pnlight")
    d.box(970, 412, 105, 60, "Essence", [], "planned")
    d.box(1085, 412, 105, 60, "Sentinel", [], "planned")
    d.box(970, 486, 220, 50, "Foresight", [], "planned")
    d.arrow([(1080, 285), (1080, 330)], kind="faint")
    d.arrow([(780, 196), (970, 196)], label_lines=["edge + new bars", "opaque series name"], kind="request", at=0.5)
    d.arrow([(970, 250), (780, 250)], "segments + new edge", "response", at=0.5)
    d.arrow([(970, 362), (780, 362)], "signed job events", "event", at=0.5)

    d.person(430, 590, "Your users")
    d.arrow([(430, 537), (430, 575)], kind="internal")
    d.legend(690, [("request", "you to Patternode"), ("response", "Patternode's answer"),
                   ("event", "event, asynchronous"), ("internal", "inside your side"), ("faint", "reads")])
    d.chip(1210, 590, "Patternode keeps none of your series · outbound only · your jurisdiction", "pn", "end")
    return d


def product_layers() -> Diagram:
    d = Diagram("products", 1240, 470, "One API, four products, one foundation",
                "Delve turns a series into shards. Essence, Sentinel and Foresight will read the same shards.",
                "Delve is the foundation: a series in, shards at every level out. Essence (what repeats), Sentinel "
                "(what moves) and Foresight (what comes next) are planned and run on Delve. All four share one API, "
                "one key and one contract.")
    d.zone(30, 100, 1180, 300, "Patternode", "pn")
    d.box(60, 300, 1120, 74, "Delve", ["the shards toolkit: a series in, segments at every level out, finished or forming"], "pn")
    d.box(60, 160, 360, 110, "Essence", ["patterns by precedent", "what repeats"], "planned", tag="planned")
    d.box(440, 160, 360, 110, "Sentinel", ["anomalies by shape", "what moves, and the alarm on it"], "planned", tag="planned")
    d.box(820, 160, 360, 110, "Foresight", ["forecasting", "what comes next"], "planned", tag="planned")
    for x in (240, 620, 1000):
        d.arrow([(x, 300), (x, 270)], kind="faint")
    d.note(40, 432, ["A series sent to Delve is not sent again for the other products: they read its shards.",
                     "Your keys, client, webhook receiver and infrastructure serve all four."], size=13)
    return d


def integration_styles() -> Diagram:
    d = Diagram("integration", 1240, 760, "Four ways to integrate",
                "Most integrations use three: a backfill once, a forming stream from then on, and events.",
                "Finished series: one synchronous REST call. Forming series: one append per bar over REST, batched "
                "REST or a gRPC stream. Backfill: upload a file, run a job, take the result. Events: webhooks, a "
                "WebSocket subscription or your event bus.")
    rows = [
        ("Finished series", "available", "History, galleries, reports", "synchronous",
         [("POST /v1/segmentations {series, bars}", "request"), ("segments, every level", "response")]),
        ("Forming series", "preview", "Live tiles; act as a segment closes", "synchronous; you keep the edge",
         [("POST /v1/segmentations/extend {series, edge, bars}", "request"),
          ("closed, right edge, a new edge to store", "response")]),
        ("Backfill", "available", "Years of history; backtests", "asynchronous",
         [("POST /v1/segmentations/jobs {source_url, result_url}", "request"), ("202; result written to your storage", "response")]),
        ("Events", "available", "Hear when something happens", "asynchronous, pushed",
         [("segmentation.job.*, account notices", "event")]),
    ]
    y = 105
    for name, status, use, mode, flows in rows:
        d.zone(30, y, 1180, 140, "", "neutral")
        d.text(56, y + 38, name, 17, 600, INK)
        d.chip(56, y + 52, status, "ok" if status == "available" else "planned")
        d.note(56, y + 96, [use, mode], 12.5, MUTED, 18)
        d.box(320, y + 25, 190, 90, "Your ingest", ["or receiver"] if name == "Events" else ["workload"], "partner")
        d.box(990, y + 25, 190, 90, "Patternode API", [], "pn")
        if len(flows) == 2:
            d.arrow([(510, y + 55), (990, y + 55)], flows[0][0], flows[0][1])
            d.arrow([(990, y + 88), (510, y + 88)], flows[1][0], flows[1][1])
        else:
            d.arrow([(990, y + 70), (510, y + 70)], flows[0][0], flows[0][1])
        y += 155
    d.note(40, 735, ["Patternode keeps nothing between calls. Forming series: REST on every plan; batched REST (1,000 series a request); gRPC on Mission Critical and Dedicated."],
           12.5)
    return d


def partner_reference() -> Diagram:
    d = Diagram("partner", 1240, 860, "Your side: the reference architecture",
                "The building blocks a production integration needs. Any stack will do; the contracts between them matter.",
                "Sources feed a collector and bar builder; the ingest workload calls Patternode with credentials from "
                "the key vault and writes segments to the segment store under each client's prefix, recording stream "
                "ids and sequences in the series registry. The event receiver verifies and queues events for workers. "
                "Your application reads the segment store. Observability covers all of it.")
    d.zone(30, 100, 210, 560, "Your client", "client")
    d.box(50, 180, 170, 80, "Historian, SCADA", ["meters, feeds"], "client")
    d.box(50, 330, 170, 80, "Market data", ["ticks, quotes, bars"], "client")
    d.box(50, 480, 170, 80, "Files", ["exports, archives"], "client")

    d.zone(270, 100, 690, 700, "Your cloud", "partner", "a trust boundary you control", dashed=True)
    d.box(300, 180, 190, 80, "1 Collector", ["reads sources", "in time order"], "partner")
    d.box(300, 330, 190, 80, "2 Bar builder", ["bars, gaps, offsets"], "partner")
    d.box(540, 255, 200, 90, "3 Ingest workload", ["Patternode client:", "hash, idempotency, retry"], "partner")
    d.box(780, 180, 160, 80, "4 Key vault", ["live key", "webhook secret"], "partner")
    d.box(780, 330, 160, 80, "5 Series registry", ["name, edge,", "version"], "partner")
    d.box(540, 455, 200, 80, "6 Segment store", ["by client, series,", "level and id"], "partner")
    d.box(300, 600, 190, 80, "7 Event receiver", ["verify, dedupe, 2xx"], "partner")
    d.box(540, 600, 200, 80, "8 Queue and workers", ["dead-letter queue"], "partner")
    d.box(780, 455, 160, 80, "9 Your app", ["renderer, API,", "for your users"], "partner")
    d.box(780, 600, 160, 80, "10 Observability", ["SLIs, traces, alerts"], "partner")

    for yy in (220, 370, 520):
        d.arrow([(220, yy), (300, yy if yy != 520 else 520), (300, yy)][:2] if yy != 520 else [(220, 520), (395, 520), (395, 410)], kind="internal")
    d.arrow([(395, 260), (395, 330)], kind="internal")
    d.arrow([(490, 370), (515, 370), (515, 315), (540, 315)], kind="internal")
    d.arrow([(780, 220), (640, 220), (640, 255)], "credentials", "faint", at=0.5)
    d.arrow([(740, 320), (780, 360)], kind="internal", both=True)
    d.arrow([(640, 345), (640, 455)], kind="internal")
    d.arrow([(740, 495), (780, 495)], kind="internal")
    d.arrow([(490, 640), (540, 640)], kind="internal")
    d.arrow([(640, 600), (640, 535)], kind="internal")

    d.zone(990, 100, 220, 700, "Patternode", "pn", "keeps nothing")
    d.box(1010, 255, 180, 90, "Patternode API", ["your jurisdiction"], "pn")
    d.arrow([(740, 280), (1010, 280)], "edge + bars", "request", at=0.62)
    d.arrow([(1010, 322), (740, 322)], "segments + edge", "response", at=0.38)
    d.arrow([(1100, 345), (1100, 720), (395, 720), (395, 680)], "signed job events", "event", at=0.5)
    d.legend(838, [("request", "to Patternode"), ("response", "answer"), ("event", "event"), ("internal", "your side"),
                   ("faint", "credentials")])
    return d


def deployment() -> Diagram:
    d = Diagram("deployment", 1240, 720, "Deployment and resilience",
                "Patternode holds no series state, so either region answers any call. Your edges are in your store.",
                "Your callers run in one or two regions of your cloud and reach the jurisdiction endpoint over the "
                "internet or private connectivity. The endpoint routes to either of Patternode's two regions in the "
                "jurisdiction, each with its own edge and cells. Stream checkpoints replicate between regions within "
                "one second; a regional failover completes within 60 seconds.")
    d.zone(30, 100, 360, 520, "Your cloud", "partner", "same cloud regions as the jurisdiction")
    d.box(60, 170, 300, 150, "Region A", ["ingest workload", "event receiver", "segments and edges (replicated)"], "partner")
    d.box(60, 400, 300, 150, "Region B", ["ingest workload", "event receiver", "segments and edges (replicated)"], "partner")
    d.arrow([(210, 320), (210, 400)], "your replication", "internal", both=True)

    d.zone(420, 100, 170, 520, "Network", "neutral")
    d.box(440, 180, 130, 110, "Private link", ["PrivateLink,", "Private Link,", "PSC"], "plain")
    d.box(440, 400, 130, 110, "Internet", ["TLS 1.3", "HTTP/2"], "plain")

    d.zone(620, 100, 590, 520, "Patternode, one jurisdiction", "pn", "anz · eu · us: processed only here, kept nowhere")
    d.box(650, 160, 530, 60, "{jurisdiction}.api.patternode.com", ["routes to the nearest healthy region"], "pnlight")
    d.box(650, 260, 250, 300, "Region 1", ["edge", "your cells", "no series state", "", "3 zones"], "pn")
    d.box(930, 260, 250, 300, "Region 2", ["edge", "your cells", "no series state", "", "3 zones"], "pn")
    d.chip(915, 575, "active-active on Mission Critical and Dedicated", "pn", "middle")
    d.arrow([(775, 220), (775, 260)], kind="response")
    d.arrow([(1055, 220), (1055, 260)], kind="response")
    d.arrow([(360, 235), (440, 235)], kind="request")
    d.arrow([(360, 455), (440, 455)], kind="request")
    d.arrow([(570, 235), (600, 235), (600, 190), (650, 190)], kind="request")
    d.arrow([(570, 455), (610, 455), (610, 200), (650, 200)], kind="request")

    rows = [("Zone fails", "nothing to see"), ("Region fails", "traffic moves within 60 s; nothing of yours was held there to lose"),
            ("Your client must", "resend unanswered requests unchanged; reconnect gRPC; dedupe events")]
    y = 655
    for k, v in rows:
        d.text(40, y, k, 12.5, 600, INK)
        d.text(190, y, v, 12.5, 400, MUTED)
        y += 20
    return d


def security() -> Diagram:
    d = Diagram("security", 1240, 660, "Trust boundaries and what crosses them",
                "Every control a request meets, from your workload to Patternode's service, and back.",
                "Requests cross from your trust boundary over TLS 1.3, optionally private connectivity, to Patternode's "
                "edge, which checks the key or token, the body hash, the scopes and the quotas before the service sees "
                "them. Only bars and an opaque series name cross; segments come back. Events come back signed.")
    d.zone(30, 100, 330, 430, "Your trust boundary", "partner", dashed=True)
    d.box(60, 160, 270, 70, "Key vault and KMS", ["keys; your edges live in your store"], "partner")
    d.box(60, 320, 270, 80, "Ingest workload", ["a live key, or a", "15-minute OAuth token"], "partner")
    d.box(60, 440, 270, 64, "Event receiver", ["verifies signatures"], "partner")
    d.arrow([(195, 230), (195, 320)], "credentials", "faint", at=0.5)

    d.zone(400, 100, 240, 430, "In transit", "neutral")
    d.note(422, 160, ["TLS 1.3 (1.2 forward-secret)", "mutual TLS, optional", "private connectivity", "IP allow list per key"],
           12.5, MUTED, 24)
    d.zone(680, 100, 250, 430, "Patternode edge", "pn")
    d.note(702, 160, ["key or token checked", "body SHA-256 checked", "scopes checked", "quotas and spend limits"],
           12.5, "#004e64", 24)
    d.zone(970, 100, 240, 430, "Patternode service", "pn")
    d.note(992, 160, ["keeps none of your series", "edges sealed: encrypted,", "signed, bound to you", "audit log, 7 years"], 12.5, "#004e64", 24)
    d.box(992, 320, 196, 110, "Delve", ["your cells", "seals edges; your", "KMS key, optional"], "pn")

    d.arrow([(330, 340), (992, 340)], "edge + bars + opaque series name", "request", at=0.27)
    d.arrow([(992, 385), (330, 385)], "segments + new sealed edge", "response", at=0.73)
    d.arrow([(1090, 430), (1090, 472), (330, 472)], "job events, signed (Standard Webhooks)", "event", at=0.5)

    d.zone(30, 555, 1180, 80, "", "neutral")
    d.text(56, 588, "Never crosses:", 13, 600, INK)
    d.text(176, 588, "your client's name, asset names, units or locations · your keys after they are created · "
                     "any connection from Patternode into your network", 13, 400, MUTED)
    d.text(56, 613, "Patternode staff never see series; support access to metadata is logged in your audit log.", 13, 400, MUTED)
    return d


def utilities() -> Diagram:
    d = Diagram("utilities", 1240, 700, "Reference: utility operations",
                "Outbound only. Patternode sits outside every control zone and electronic security perimeter.",
                "SCADA and the historian sit in the operational zone. A one-way transfer mirrors the historian into "
                "the DMZ. The ingest workload in the enterprise zone or your cloud reads the mirror and calls Patternode "
                "in the ANZ jurisdiction over private connectivity. Events return to a receiver in the enterprise zone. "
                "Nothing connects into the operational zone.")
    d.zone(30, 100, 300, 500, "Operational zone", "ot", "control systems, the perimeter")
    d.box(60, 170, 240, 80, "RTUs, PLCs, IEDs", ["field devices"], "ot")
    d.box(60, 300, 240, 80, "SCADA", ["control, alarms"], "ot")
    d.box(60, 430, 240, 90, "Historian", ["compressed archive", "with quality codes"], "ot")
    d.arrow([(180, 250), (180, 300)], kind="internal")
    d.arrow([(180, 380), (180, 430)], kind="internal")

    d.zone(360, 100, 210, 500, "DMZ", "neutral")
    d.box(380, 430, 170, 90, "Historian mirror", ["read-only replica"], "plain")
    d.arrow([(300, 475), (380, 475)], "one-way", "oneway", at=0.5)

    d.zone(600, 100, 340, 500, "Enterprise zone or your cloud", "partner")
    d.box(630, 430, 280, 90, "Ingest workload", ["good-quality points only", "bars from kept points"], "partner")
    d.box(630, 300, 280, 80, "Segment store", ["segments and edges, per client"], "partner")
    d.box(630, 170, 280, 80, "Control room tools", ["galleries, live tiles"], "partner")
    d.box(770, 545, 140, 40, "Event receiver", [], "partner")
    d.arrow([(550, 475), (630, 475)], kind="internal")
    d.arrow([(700, 430), (700, 380)], kind="internal")
    d.arrow([(770, 300), (770, 250)], kind="internal")

    d.zone(970, 100, 240, 500, "Patternode ANZ", "pn", "processed in AU and NZ, kept nowhere")
    d.box(990, 310, 200, 210, "Patternode API", ["Mission Critical", "private connectivity", "mutual TLS"], "pn")
    d.arrow([(910, 475), (990, 475)], "edge + bars", "request", at=0.5)
    d.arrow([(990, 340), (910, 340)], "segments + edge", "response", at=0.5)
    d.arrow([(1090, 520), (1090, 565), (910, 565)], "events", "event", at=0.5)
    d.note(40, 640, ["Blackout periods: register storm and emergency declarations; Patternode releases nothing to your cells inside them.",
                     "Capacity: size for the storm (every point reporting at once, then backfill after an outage), not the calm day."], 12.5)
    return d


def finance() -> Diagram:
    d = Diagram("finance", 1240, 700, "Reference: quantitative trading",
                "One path for research, one for live; the same profile version on both, so backtest and live agree.",
                "Market data reaches a feed handler and a tick store. The live path builds bars and streams them over "
                "gRPC to Patternode in the same region, and a subscription returns stream events to the signal engine. "
                "The research path uploads Parquet to jobs and stores results for backtests. Both pin the same profile "
                "version.")
    d.zone(30, 100, 220, 500, "Venues and vendors", "client")
    d.box(50, 200, 180, 90, "Market data", ["trades, quotes", "ns timestamps"], "client")
    d.box(50, 400, 180, 90, "Vendor history", ["bars, ticks"], "client")

    d.zone(280, 100, 640, 500, "Your trading platform", "partner", "co-located with the jurisdiction's region")
    d.box(310, 200, 170, 90, "Feed handler", ["normalises, times"], "partner")
    d.box(740, 160, 160, 80, "Bar builder", ["bars, edges kept", "per instrument"], "partner")
    d.box(740, 265, 160, 70, "Signal engine", ["your models"], "partner")
    d.box(520, 265, 170, 70, "Order management", [], "partner")
    d.box(310, 400, 170, 90, "Tick store", ["your history"], "partner")
    d.box(740, 390, 160, 80, "Research jobs", ["Parquet in your storage"], "partner")
    d.box(740, 500, 160, 70, "Backtests", ["segments per version"], "partner")
    d.arrow([(230, 245), (310, 245)], kind="internal")
    d.arrow([(230, 445), (310, 445)], kind="internal")
    d.arrow([(480, 215), (610, 215), (610, 195), (740, 195)], kind="internal")
    d.arrow([(395, 290), (395, 400)], kind="internal")
    d.arrow([(480, 430), (740, 430)], kind="internal")
    d.arrow([(740, 300), (690, 300)], kind="internal")
    d.arrow([(820, 470), (820, 500)], kind="internal")
    d.chip(610, 150, "LIVE", "tag", "middle")
    d.chip(610, 380, "RESEARCH", "tag", "middle")

    d.zone(950, 100, 260, 500, "Patternode, same region", "pn")
    d.box(975, 165, 210, 145, "gRPC Extend", ["edge + bars in,", "segments + edge out", "p99 10 ms at the edge"], "pn")
    d.box(975, 390, 210, 90, "Jobs", ["reads and writes", "your storage"], "pn")
    d.arrow([(900, 190), (975, 190)], "edge + bars", "request", at=0.5)
    d.arrow([(975, 290), (900, 290)], "segments", "response", at=0.5)
    d.arrow([(900, 415), (975, 415)], "links", "request", at=0.5)
    d.arrow([(975, 455), (900, 455)], "done", "event", at=0.5)
    d.chip(450, 540, "profile pinned: standard@2026-11 on both paths", "pn", "middle")
    d.note(40, 640, ["Blackout periods: register your venues' trading hours; nothing changes in your cells while you trade.",
                     "Capacity: size for the open and the close, when every instrument trades at once."], 12.5)
    return d


# Quant funds --------------------------------------------------------------------------


def quant_context() -> Diagram:
    d = Diagram("quant-context", 1240, 700, "A quant fund with Patternode",
                "Research and live share one contract and one pinned profile version. Patternode holds none of the fund's data.",
                "Market data and alternative data come from venues and vendors into the fund's data platform. "
                "Research builds bars, runs jobs over files in the fund's storage, and backtests on the segments. "
                "The live platform extends each instrument from its stored edge and feeds the signal engine, which "
                "sends orders to venues. Risk and compliance read the same stored segments.")
    d.zone(30, 100, 220, 520, "Venues and vendors", "client")
    d.box(50, 170, 180, 80, "Exchanges", ["trades, quotes"], "client")
    d.box(50, 300, 180, 80, "Data vendors", ["history, reference"], "client")
    d.box(50, 430, 180, 80, "Brokers", ["orders, fills"], "client")

    d.zone(280, 100, 640, 520, "The fund", "partner", "its cloud or co-location, its storage, its keys")
    d.box(310, 170, 180, 80, "Data platform", ["tick store, lake"], "partner")
    d.box(530, 170, 170, 80, "Research", ["jobs, backtests"], "partner")
    d.box(740, 170, 150, 80, "Model registry", ["pinned versions"], "partner")
    d.box(310, 330, 180, 90, "Live platform", ["bars, edges kept", "per instrument"], "partner")
    d.box(530, 330, 170, 90, "Signal engine", ["your models"], "partner")
    d.box(740, 330, 150, 90, "Execution", ["OMS, EMS"], "partner")
    d.box(310, 480, 580, 70, "Segment store", ["segments and edges, per strategy and instrument; read by risk and compliance"], "partner")
    d.arrow([(230, 210), (310, 210)], kind="internal")
    d.arrow([(230, 340), (270, 340), (270, 230), (310, 230)], kind="internal")
    d.arrow([(490, 210), (530, 210)], kind="internal")
    d.arrow([(700, 210), (740, 210)], kind="internal")
    d.arrow([(400, 250), (400, 330)], kind="internal")
    d.arrow([(490, 375), (530, 375)], kind="internal")
    d.arrow([(700, 375), (740, 375)], kind="internal")
    d.arrow([(815, 420), (815, 450), (260, 450), (260, 470), (230, 470)], kind="internal")
    d.arrow([(400, 420), (400, 480)], kind="internal", both=True)
    d.arrow([(815, 250), (815, 330)], "same version", "faint", at=0.5)

    d.zone(950, 100, 260, 520, "Patternode", "pn", "your jurisdiction; keeps nothing")
    d.box(975, 170, 210, 90, "Jobs", ["read and write", "your storage"], "pn")
    d.box(975, 330, 210, 90, "Extend", ["REST, batch or gRPC"], "pn")
    d.arrow([(615, 170), (615, 155), (960, 155), (960, 195), (975, 195)], "links to files", "request", at=0.6)
    d.arrow([(975, 240), (935, 240), (935, 268), (640, 268), (640, 250)], "done", "event", at=0.5)
    d.arrow([(490, 350), (512, 350), (512, 290), (945, 290), (945, 350), (975, 350)], "edge + bars", "request", at=0.4)
    d.arrow([(975, 400), (957, 400), (957, 312), (455, 312), (455, 330)], "segments + edge", "response", at=0.62)
    d.legend(660, [("request", "to Patternode"), ("response", "answer"), ("event", "event"), ("internal", "the fund's side")])
    return d


def quant_research() -> Diagram:
    d = Diagram("quant-research", 1240, 600, "Research and backtest",
                "Files stay in the fund's storage. Jobs read them and write results back; nothing is kept at Patternode.",
                "The research platform writes bars to Parquet in its own storage, presigns links, and runs a "
                "Patternode job per series. Results land in the fund's storage, keyed by profile version, and feed "
                "features and backtests. Each series' edge is kept to hand over to live trading.")
    d.zone(30, 100, 880, 420, "The fund's research platform", "partner")
    d.box(60, 170, 170, 90, "Tick store", ["point in time"], "partner")
    d.box(270, 170, 170, 90, "Bar builder", ["Parquet, ns times"], "partner")
    d.box(480, 170, 180, 90, "Your storage", ["in/, out/ by version"], "partner")
    d.box(700, 170, 180, 90, "Job runner", ["presigns, submits,", "awaits events"], "partner")
    d.box(480, 360, 180, 90, "Feature builder", ["levels, trends, shapes"], "partner")
    d.box(700, 360, 180, 90, "Backtester", ["segments per version"], "partner")
    d.box(60, 360, 380, 90, "Model registry", ["model, data window, profile version, edges at the end"], "partner")
    d.arrow([(230, 215), (270, 215)], kind="internal")
    d.arrow([(440, 215), (480, 215)], kind="internal")
    d.arrow([(660, 215), (700, 215)], kind="internal")
    d.arrow([(570, 260), (570, 360)], kind="internal")
    d.arrow([(660, 405), (700, 405)], kind="internal")
    d.arrow([(700, 430), (440, 430)], kind="internal")
    d.zone(940, 100, 270, 420, "Patternode", "pn", "keeps nothing")
    d.box(965, 200, 220, 140, "Jobs", ["GET your file,", "PUT the result,", "event when done"], "pn")
    d.arrow([(880, 200), (965, 200)], "links", "request", at=0.5)
    d.arrow([(965, 320), (900, 320), (900, 290), (660, 290), (660, 250)], "result written", "response", at=0.55)
    d.note(40, 555, ["Pin the profile version (standard@2026-11) in every job and record it in the model registry. Ask for return_edge",
                     "on the last window, so live trading carries on from exactly where the backtest ended."], 12.5)
    return d


def quant_live() -> Diagram:
    d = Diagram("quant-live", 1240, 640, "Live trading and its latency budget",
                "Each instrument is extended from its edge as its bar closes; the answer feeds the signal directly.",
                "Market data reaches the feed handler; the bar builder closes bars and keeps each instrument's edge in "
                "memory and in a durable store. One gRPC connection extends every instrument from its edge; the "
                "segments go to the signal engine and on to execution. Below, the latency budget from a bar's close to "
                "an order, with Patternode's share at the edge.")
    d.zone(30, 100, 900, 300, "The fund's live platform", "partner", "in the jurisdiction's cloud region, connected privately")
    d.box(60, 170, 160, 90, "Feed handler", ["ns times"], "partner")
    d.box(260, 170, 170, 90, "Bar builder", ["closes bars"], "partner")
    d.box(470, 170, 180, 90, "Extender", ["edge cache in memory,", "durable edge store"], "partner")
    d.box(690, 170, 210, 90, "Signal engine", ["segments in, signals out"], "partner")
    d.box(690, 300, 210, 70, "Execution", ["OMS, EMS, venue"], "partner")
    d.box(470, 300, 180, 70, "Segment store", ["for risk, replay"], "partner")
    d.arrow([(220, 215), (260, 215)], kind="internal")
    d.arrow([(430, 215), (470, 215)], kind="internal")
    d.arrow([(795, 260), (795, 300)], kind="internal")
    d.arrow([(560, 260), (560, 300)], kind="internal")
    d.zone(960, 100, 250, 300, "Patternode", "pn", "same region; keeps nothing")
    d.box(985, 170, 200, 120, "gRPC Extend", ["many instruments,", "one connection", "p99 10 ms at the edge"], "pn")
    d.arrow([(560, 170), (560, 155), (965, 155), (965, 190), (985, 190)], "edge + bars", "request", at=0.6)
    d.arrow([(985, 250), (940, 250), (940, 230), (900, 230)], "segments + edge", "response", at=0.5)

    budget = [("build, send", 2, "#7077ff"), ("network", 1, "#c6cddc"),
              ("Patternode p99", 10, "#0099c0"), ("network", 1, "#c6cddc"), ("signal", 5, "#7077ff"),
              ("order out", 3, "#7077ff")]
    d.text(40, 450, "An example latency budget, milliseconds at p99", 14, 600, INK)
    x, scale = 40, 40
    for label, ms, colour in budget:
        if ms == 0:
            d.body.append(f'<rect x="{x}" y="470" width="4" height="44" fill="{colour}"/>')
            d.text(x, 532, label, 11.5, 500, MUTED)
            x += 8
            continue
        w = ms * scale
        d.body.append(f'<rect x="{x}" y="470" width="{w - 4}" height="44" rx="6" fill="{colour}" opacity="0.9"/>')
        d.text(x + (w - 4) / 2, 497, f"{ms} ms", 12, 600, "#ffffff", "middle")
        d.text(x + (w - 4) / 2, 532, label, 11.5, 500, MUTED, "middle")
        x += w
    d.text(x + 12, 497, "= 22 ms, bar close to order", 13, 600, INK)
    d.note(40, 580, ["Your figures will differ: measure your own share; Patternode's is in server-timing on every answer.",
                     "Keep edges in memory for speed and in a durable store for restarts; write both before acting on a signal."], 12.5)
    return d


def quant_versions() -> Diagram:
    d = Diagram("quant-versions", 1240, 520, "Reproducibility across profile versions",
                "A version never changes. Moving to a new one is a decision you take, with both running side by side.",
                "Profile version 2026-11 is used for the backtest and for live trading. When version 2027-05 is "
                "published, the fund re-runs its research on it as jobs and shadows it live beside the old version, "
                "then switches. The old version stays served for at least 24 months, so every past result reproduces.")
    d.zone(30, 100, 1180, 330, "", "neutral")
    d.text(60, 140, "standard@2026-11", 14, 600, "#004e64", mono=True)
    d.body.append('<rect x="60" y="155" width="1120" height="26" rx="13" fill="#d5f2fe"/>')
    d.text(1170, 173, "served at least 24 months after its successor", 11.5, 500, "#004e64", "end")
    d.text(60, 240, "standard@2027-05", 14, 600, "#352da5", mono=True)
    d.body.append('<rect x="560" y="255" width="620" height="26" rx="13" fill="#e8ecff"/>')
    stages = [(90, "Backtest", "jobs on 2026-11"), (300, "Live", "extend on 2026-11"), (570, "Re-run research", "jobs on 2027-05"),
              (790, "Shadow live", "both versions, compare"), (1010, "Switch", "new edges from 2027-05")]
    for x, title, sub in stages:
        d.box(x, 320, 170, 80, title, [sub], "partner")
    for a, b in [(260, 300), (470, 570), (740, 790), (960, 1010)]:
        d.arrow([(a, 360), (b, 360)], kind="internal")
    d.note(40, 470, ["An edge is bound to its version: a series switches by starting again on the new version (a finished series with",
                     "return_edge), never by sending an old edge with a new version. Record the version beside every stored result."], 12.5)
    return d


ALL = [system_context, product_layers, integration_styles, partner_reference, deployment, security, utilities, finance,
       quant_context, quant_research, quant_live, quant_versions]


def main() -> int:
    check = "--check" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    stale = []
    for make in ALL:
        d = make()
        path = OUT / f"{d.name}.svg"
        svg = d.svg()
        if check:
            if not path.exists() or path.read_text() != svg:
                stale.append(path.name)
        else:
            path.write_text(svg)
    if stale:
        print("Out of date, run python website/diagrams/architecture.py:", ", ".join(stale))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(ALL)} diagrams in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
