"""Cached, antialiased directions for the most recently completed move."""
from functools import lru_cache
from math import hypot, sqrt

from PIL import Image, ImageDraw

from ..game import Move

MOVE_COLOR = '#5266dc'
SHOT_COLOR = '#168894'


def _direction(draw, start, end, cell, color, dashed, start_radius, end_radius, lane):
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = hypot(dx, dy)
    ux, uy = dx/length, dy/length
    # Intersect each lane with the marker circles so shifted lines still connect.
    start_inset = cell*sqrt(start_radius**2-lane**2)
    end_inset = cell*sqrt(end_radius**2-lane**2)
    offset = cell*lane
    start = (start[0]-uy*offset+ux*start_inset, start[1]+ux*offset+uy*start_inset)
    end = (end[0]-uy*offset-ux*end_inset, end[1]+ux*offset-uy*end_inset)
    visible = length-start_inset-end_inset
    width = max(3, round(cell*.035))
    head = min(cell*.12, visible*.42)
    shaft = visible-head*.65
    distance = 0
    while distance < shaft:
        finish = min(distance+cell*.10, shaft) if dashed else shaft
        a = (start[0]+ux*distance, start[1]+uy*distance)
        b = (start[0]+ux*finish, start[1]+uy*finish)
        draw.line((a, b), fill='white', width=width+4)
        draw.line((a, b), fill=color, width=width)
        distance = finish+cell*.065
    base = (end[0]-ux*head, end[1]-uy*head)
    draw.polygon((end, (base[0]-uy*head*.55, base[1]+ux*head*.55),
                  (base[0]+uy*head*.55, base[1]-ux*head*.55)), fill=color)


@lru_cache(maxsize=8)
def trail(size: int, move: Move):
    """Return a transparent overlay, scaled only when the move or size changes."""
    factor = 3
    image = Image.new('RGBA', ((size+1)*factor, (size+1)*factor))
    draw = ImageDraw.Draw(image)
    cell = size*factor/10
    source, target, arrow = [((col+.5)*cell, (row+.5)*cell) for row, col in move]
    move_dr, move_dc = (move[1][i]-move[0][i] for i in (0, 1))
    shot_dr, shot_dc = (move[2][i]-move[1][i] for i in (0, 1))
    retraces = (move_dr*shot_dc == move_dc*shot_dr
                and move_dr*shot_dr+move_dc*shot_dc < 0)
    # A shared positive offset puts opposite directions on opposite sides.
    lane = .07 if retraces else 0
    source_radius = .36 if move[0] == move[2] else .14
    _direction(draw, source, target, cell, MOVE_COLOR, False, source_radius, .40, lane)
    _direction(draw, target, arrow, cell, SHOT_COLOR, True, .40, .36, lane)
    markers = [(target, .40, MOVE_COLOR), (arrow, .36, SHOT_COLOR)]
    if move[0] != move[2]:
        markers.append((source, .14, MOVE_COLOR))
    for center, radius, color in markers:
        x, y = center
        radius *= cell
        bounds = (x-radius, y-radius, x+radius, y+radius)
        draw.ellipse(bounds, outline=color, width=max(3, round(cell*.018)))
    return image.resize((size+1, size+1), Image.Resampling.LANCZOS)
