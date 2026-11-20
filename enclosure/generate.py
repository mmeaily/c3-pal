"""
c3-pal enclosure generator
==========================

Units: millimetres

A flat bar for the c3-pal hydration buddy, worn upright on the side of a
water bottle (Owala FreeSip and the like, about 68-80 mm across) with
two hook-and-loop straps.  All the parts lie side by side in one layer,
so the bar is as thin as the battery allows.  From the bottom end up:

    C3 board    ESP32-C3 0.42in OLED, face down behind a window in the
                front; its USB-C comes out of the bottom end (PRG).
    battery     LP702030, on the floor.
    screw       one M3 screw from the front, into a nut in the lid.
    TP4056      mini USB-C charger; its USB-C comes out of the top end
                (PWR).

    front (tub)  window with a bevelled edge, a flexing tab over the
                 BOOT button (the "I drank" button), a pin hole over
                 RST, PRG / PWR engraved by their ends, and four ears
                 with slots for the straps.
    back (lid)   two rails along its long edges rest on the bottle; its
                 bottom edge tucks under a lip in the PRG end wall.

Requires:
    CadQuery, matplotlib (preview only)

Run:
    python generate.py

Output (in this folder):
    c3pal_base.stl      front (tub), front face on the bed
    c3pal_lid.stl       back (lid), rails on the bed
    c3pal_preview.png   front / assembled / exploded / on the bottle /
                        section / back views

Coordinates: X along the bar, X = 0 the inside face of the PRG (bottom)
end wall, +X up the bar.  Y across, +Y to the right seen from the front
with the PRG end down.  Z from the front face (Z = 0, the print bed for
the tub) towards the bottle.

Assembly:
    1. Battery on the floor (tape), PCM end up.  TP4056 at the top end,
       USB-C into the PWR opening (tape).  Solder battery -> B+/B-,
       OUT+/OUT- -> the C3's 5V/GND; run the wires over the battery.
    2. C3 face down onto its ribs, USB-C into the PRG opening.
    3. Slide the lid's bottom edge into the PRG wall's slot and lower it.
    4. Drop the nut into the hex pocket in the back, screw in from the
       front with the washer.
    5. Thread a one-wrap strap through each pair of ears, round the
       bottle, and pull tight.
"""

import json
import math
import sys
from pathlib import Path

import cadquery as cq


# ============================================================
# PARAMETERS
# ============================================================

HERE = Path(__file__).parent
PARAMS_FILE = HERE / "params.json"
OUTPUT_PREFIX = "c3pal"


def load_params(path):
    """
    Read a grouped parameter file into a flat {name: value} dict.
    Groups and keys starting with '_' are notes and are skipped.
    """

    try:
        with open(path, encoding="utf-8") as file:
            groups = json.load(file)
    except FileNotFoundError:
        sys.exit(f"Parameter file not found: {path}")
    except json.JSONDecodeError as error:
        sys.exit(f"{path}: invalid JSON - {error}")

    flat = {}
    for group, values in groups.items():
        if group.startswith("_"):
            continue
        for name, value in values.items():
            if name.startswith("_"):
                continue
            if name in flat:
                sys.exit(f"{path}: '{name}' appears more than once")
            flat[name] = value
    return flat


_params = load_params(PARAMS_FILE)


def param(name):
    try:
        return _params.pop(name)
    except KeyError:
        sys.exit(f"{PARAMS_FILE}: missing parameter '{name}'")


# C3 board
C3_LENGTH = param("C3_LENGTH")
C3_WIDTH = param("C3_WIDTH")
C3_PCB = param("C3_PCB")
C3_UNDER = param("C3_UNDER")
C3_OLED_HEIGHT = param("C3_OLED_HEIGHT")
C3_USB_OVERHANG = param("C3_USB_OVERHANG")
C3_USB_WIDTH = param("C3_USB_WIDTH")
C3_USB_HEIGHT = param("C3_USB_HEIGHT")
C3_BUTTON_FROM_END = param("C3_BUTTON_FROM_END")
C3_BUTTON_FROM_SIDE = param("C3_BUTTON_FROM_SIDE")
C3_BUTTON_HEIGHT = param("C3_BUTTON_HEIGHT")
C3_BOOT_SIDE = param("C3_BOOT_SIDE")
C3_SCREEN_FROM_END = param("C3_SCREEN_FROM_END")
C3_SCREEN_OFFSET = param("C3_SCREEN_OFFSET")
C3_SCREEN_WIDTH = param("C3_SCREEN_WIDTH")
C3_SCREEN_HEIGHT = param("C3_SCREEN_HEIGHT")
C3_GLASS_FROM_END = param("C3_GLASS_FROM_END")
C3_GLASS_LENGTH = param("C3_GLASS_LENGTH")
C3_GLASS_WIDTH = param("C3_GLASS_WIDTH")

# Charger
TP_LENGTH = param("TP_LENGTH")
TP_WIDTH = param("TP_WIDTH")
TP_PCB = param("TP_PCB")
TP_PARTS = param("TP_PARTS")
TP_USB_OVERHANG = param("TP_USB_OVERHANG")
TP_USB_WIDTH = param("TP_USB_WIDTH")
TP_USB_HEIGHT = param("TP_USB_HEIGHT")
TP_USB_OFFSET = param("TP_USB_OFFSET")

# Battery
BATT_LENGTH = param("BATT_LENGTH")
BATT_WIDTH = param("BATT_WIDTH")
BATT_THICKNESS = param("BATT_THICKNESS")

# Case
WALL = param("WALL")
PORT_WALL = param("PORT_WALL")
FLOOR = param("FLOOR")
LID = param("LID")
CORNER_RADIUS = param("CORNER_RADIUS")
CLEARANCE = param("CLEARANCE")
FRONT_GAP = param("FRONT_GAP")
WIRE_GAP = param("WIRE_GAP")
PORT_INSET = param("PORT_INSET")
PORT_CLEARANCE = param("PORT_CLEARANCE")
LEDGE = param("LEDGE")
SEAT = param("SEAT")
LIP = param("LIP")
LIP_THICKNESS = param("LIP_THICKNESS")
PEG = param("PEG")

# Mount
BOTTLE_MIN_DIAMETER = param("BOTTLE_MIN_DIAMETER")
BOTTLE_MAX_DIAMETER = param("BOTTLE_MAX_DIAMETER")
RAIL_CLEARANCE = param("RAIL_CLEARANCE")
STRAP_WIDTH = param("STRAP_WIDTH")
STRAP_SLOT = param("STRAP_SLOT")
STRAP_INSET = param("STRAP_INSET")
EAR_RIM = param("EAR_RIM")
EAR_THICKNESS = param("EAR_THICKNESS")

# Screen
WINDOW_MARGIN = param("WINDOW_MARGIN")
WINDOW_CHAMFER = param("WINDOW_CHAMFER")
BEZEL_MARGIN = param("BEZEL_MARGIN")
BEZEL_GAP = param("BEZEL_GAP")

# Buttons
FLEX_WIDTH = param("FLEX_WIDTH")
FLEX_LENGTH = param("FLEX_LENGTH")
FLEX_SLOT = param("FLEX_SLOT")
FLEX_THICKNESS = param("FLEX_THICKNESS")
NUB_DIAMETER = param("NUB_DIAMETER")
NUB_GAP = param("NUB_GAP")
RST_HOLE = param("RST_HOLE")

# Screws
SCREW_LENGTHS = param("SCREW_LENGTHS")
SCREW_HEAD_DIAMETER = param("SCREW_HEAD_DIAMETER")
SCREW_HEAD_HEIGHT = param("SCREW_HEAD_HEIGHT")
WASHER_DIAMETER = param("WASHER_DIAMETER")
WASHER_THICKNESS = param("WASHER_THICKNESS")
HEAD_CLEARANCE = param("HEAD_CLEARANCE")
SCREW_HOLE = param("SCREW_HOLE")
NUT_FLATS = param("NUT_FLATS")
NUT_THICKNESS = param("NUT_THICKNESS")
NUT_FIT = param("NUT_FIT")
NUT_PAST = param("NUT_PAST")
BOSS_WALL = param("BOSS_WALL")

# Labels
LABEL_SIZE = param("LABEL_SIZE")
LABEL_DEPTH = param("LABEL_DEPTH")
LABEL_FONT = param("LABEL_FONT")

# Output
PREVIEW = param("PREVIEW")
CHECK_FIT = param("CHECK_FIT")
PLA_DENSITY = param("PLA_DENSITY")

if _params:
    sys.exit(f"{PARAMS_FILE}: unknown parameter(s): {', '.join(sorted(_params))}")

if C3_BOOT_SIDE not in ("left", "right"):
    sys.exit(f"C3_BOOT_SIDE must be 'left' or 'right', not '{C3_BOOT_SIDE}'")

PREVIEW_FILE = f"{OUTPUT_PREFIX}_preview.png"
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.1

errors = []


def error(message):
    errors.append(message)
    print(f"ERROR: {message}")


# ============================================================
# LAYOUT
# ============================================================

# --- across (Y) ---
inner_half = max(C3_WIDTH, BATT_WIDTH, TP_WIDTH) / 2.0 + CLEARANCE
outer_half = inner_half + WALL

# --- depth (Z), front to back ---
# C3 face down: its component side (screen, buttons, USB-C) faces the
# front.  The USB-C receptacle is the tallest part on that side.
c3_face = FLOOR + FRONT_GAP + C3_USB_HEIGHT   # component side of the PCB
c3_back = c3_face + C3_PCB
c3_usb_z = c3_face - C3_USB_HEIGHT / 2.0
glass_front = c3_face - C3_OLED_HEIGHT
button_front = c3_face - C3_BUTTON_HEIGHT

batt_z0 = FLOOR
batt_z1 = batt_z0 + BATT_THICKNESS

tp_z0 = FLOOR                                 # PCB on the floor, parts to the back
tp_top = tp_z0 + TP_PCB
tp_usb_z = tp_top + TP_USB_HEIGHT / 2.0
tp_z1 = tp_top + max(TP_USB_HEIGHT, TP_PARTS)

lid_z0 = max(batt_z1 + WIRE_GAP, c3_back + C3_UNDER + WIRE_GAP, tp_z1 + 0.3)
lid_z1 = lid_z0 + LID

# The lid sits in a pocket SEAT into the walls; above it the side walls
# stand on as rails that rest on the bottle, tall enough that the
# smallest bottle, resting on their inner edges, clears the lid.
# edges, clears the lid between them.
rail_in = inner_half + SEAT                  # inner edge of the rails
r_min = BOTTLE_MIN_DIAMETER / 2.0
rail_h = r_min - math.sqrt(r_min ** 2 - rail_in ** 2) + RAIL_CLEARANCE
rail_top = lid_z1 + rail_h

port_h = {"PRG": C3_USB_HEIGHT + PORT_CLEARANCE, "PWR": TP_USB_HEIGHT + PORT_CLEARANCE}
port_w = {"PRG": C3_USB_WIDTH + PORT_CLEARANCE, "PWR": TP_USB_WIDTH + PORT_CLEARANCE}

if c3_usb_z - port_h["PRG"] / 2.0 < 0.5:
    error("the PRG opening runs into the front face")

# --- along (X), bottom (PRG) end up ---
c3_face_x = -PORT_INSET                       # C3 receptacle face
c3_x0 = c3_face_x + C3_USB_OVERHANG           # PCB bottom edge
c3_x1 = c3_x0 + C3_LENGTH
batt_x0 = c3_x1 + CLEARANCE
batt_x1 = batt_x0 + BATT_LENGTH

nut_corner_r = (NUT_FLATS + NUT_FIT) / math.sqrt(3.0)
boss_r = nut_corner_r + BOSS_WALL
post_x = batt_x1 + CLEARANCE + boss_r
post_y = 0.0

tp_x0 = post_x + boss_r + CLEARANCE
tp_x1 = tp_x0 + TP_LENGTH
tp_face_x = tp_x1 + TP_USB_OVERHANG           # TP receptacle face
tp_y = -TP_USB_OFFSET                         # board centre, so the USB-C is on Y = 0
inner_length = tp_face_x - PORT_INSET
outer_x0 = -PORT_WALL
outer_x1 = inner_length + PORT_WALL

pocket_x1 = inner_length + SEAT               # lid pocket, far end
lid_x0 = 0.15                                 # under the lips at the PRG end
lid_x1 = pocket_x1 - LIP - 0.25               # room to slide it under them

if abs(tp_y) + TP_WIDTH / 2.0 > inner_half:
    error("the TP4056 is too wide for the bar the way round it is placed")

# --- C3 features ---
boot_sign = 1.0 if C3_BOOT_SIDE == "right" else -1.0
button_x = c3_x1 - C3_BUTTON_FROM_END
boot_y = boot_sign * (C3_WIDTH / 2.0 - C3_BUTTON_FROM_SIDE)
rst_y = -boot_y

screen_x = c3_x1 - C3_SCREEN_FROM_END
screen_y = -C3_SCREEN_OFFSET
window_hx = C3_SCREEN_HEIGHT / 2.0 + WINDOW_MARGIN   # along
window_hy = C3_SCREEN_WIDTH / 2.0 + WINDOW_MARGIN    # across
bezel_hx = window_hx + BEZEL_MARGIN
bezel_hy = window_hy + BEZEL_MARGIN
bezel_z1 = max(glass_front - BEZEL_GAP, FLOOR)

glass_x1 = c3_x1 - C3_GLASS_FROM_END
glass_x0 = glass_x1 - C3_GLASS_LENGTH

# BOOT flexure: hinged on the window side, nub over the button.
flex_x1 = button_x + NUB_DIAMETER / 2.0 + 1.0
flex_x0 = flex_x1 - FLEX_LENGTH
flex_hy = FLEX_WIDTH / 2.0

# --- strap ears ---
ear_xs = [outer_x0 + STRAP_INSET, outer_x1 - STRAP_INSET]
ear_hx = STRAP_WIDTH / 2.0 + 0.3 + EAR_RIM
ear_reach = 0.6 + STRAP_SLOT + EAR_RIM        # how far an ear sticks out of the side wall

# --- screw (from the front, washer under the head, nut in the lid) ---
head_depth = SCREW_HEAD_HEIGHT + WASHER_THICKNESS + 0.3
max_tip = lid_z1 - 0.3                        # stays inside the lid's back
screw_length = None
for length in sorted(SCREW_LENGTHS, reverse=True):
    tip = head_depth + length
    if tip <= max_tip and tip - NUT_PAST - NUT_THICKNESS - BOSS_WALL - 0.2 >= head_depth + 1.0:
        screw_length = length
        break
if screw_length is None:
    error("no screw length fits")
    screw_length = min(SCREW_LENGTHS)
screw_tip = head_depth + screw_length
nut_z0 = screw_tip - NUT_PAST - NUT_THICKNESS   # front face of the nut
boss_z0 = nut_z0 - BOSS_WALL                     # lid boss reaches down to here
post_z1 = boss_z0 - 0.2                          # tub post top

# --- sanity checks ---
if flex_x0 < screen_x + bezel_hx + 0.4 and abs(boot_y) - flex_hy - FLEX_SLOT < abs(screen_y) + bezel_hy:
    error(f"BOOT flexure (hinge x = {flex_x0:.1f}) runs into the screen bezel "
          f"(ends x = {screen_x + bezel_hx:.1f}); shorten FLEX_LENGTH")
if abs(boot_y) + flex_hy + FLEX_SLOT > inner_half - 0.5:
    error("BOOT flexure is too close to the side wall")
if SEAT > min(WALL, PORT_WALL) - 0.5:
    error("SEAT leaves the walls round the lid too thin")
if button_front - NUB_GAP <= FLEX_THICKNESS:
    error("BOOT button is too close to the front for a nub")


# ============================================================
# HELPERS
# ============================================================

def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cylinder_z(radius, z0, z1, x=0.0, y=0.0):
    return (cq.Workplane("XY").circle(radius).extrude(z1 - z0)
            .translate((x, y, z0)))


def hex_z(flats, z0, z1, x=0.0, y=0.0):
    return (cq.Workplane("XY").polygon(6, flats * 2.0 / math.sqrt(3.0)).extrude(z1 - z0)
            .translate((x, y, z0)))


def volume(shape):
    return sum(solid.Volume() for solid in shape.solids().vals())


def union_all(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.union(shape)
    return result


def to_bed(shape):
    bb = shape.val().BoundingBox()
    return shape.translate((0, 0, -bb.zmin))


def bottle(diameter, gap=0.05):
    """The bottle, resting on the rails' inner edges, along X."""

    r = diameter / 2.0
    zc = rail_top + math.sqrt(r * r - rail_in * rail_in) + gap
    return (cq.Workplane("YZ").center(0.0, zc).circle(r)
            .extrude(outer_x1 - outer_x0 + 40.0).translate((outer_x0 - 20.0, 0, 0)))


# ============================================================
# PARTS IN THE CASE (for the fit check and the preview)
# ============================================================

def usb_receptacle(x_face, direction, width, height, z_mid, length=7.35):
    x0, x1 = (x_face, x_face + length) if direction > 0 else (x_face - length, x_face)
    return (box(x0, x1, -width / 2.0, width / 2.0, z_mid - height / 2.0, z_mid + height / 2.0)
            .edges("|X").fillet(height / 2.0 - 0.05))


battery = box(batt_x0, batt_x1, -BATT_WIDTH / 2.0, BATT_WIDTH / 2.0, batt_z0, batt_z1)

tp_pcb = box(tp_x0, tp_x1, tp_y - TP_WIDTH / 2.0, tp_y + TP_WIDTH / 2.0, tp_z0, tp_top)
tp_usb = usb_receptacle(tp_face_x, -1, TP_USB_WIDTH, TP_USB_HEIGHT, tp_usb_z)
tp_parts = box(tp_x0 + 1.0, tp_x1 - 8.0, tp_y - TP_WIDTH / 2.0 + 1.0, tp_y + TP_WIDTH / 2.0 - 1.0,
               tp_top, tp_top + TP_PARTS)

c3_pcb = (box(c3_x0, c3_x1, -C3_WIDTH / 2.0, C3_WIDTH / 2.0, c3_face, c3_back)
          .edges("|Z").fillet(1.0))
c3_under = box(c3_x0 + 2.0, c3_x1 - 2.0, -C3_WIDTH / 2.0 + 3.0, C3_WIDTH / 2.0 - 3.0,
               c3_back, c3_back + C3_UNDER)
c3_usb = usb_receptacle(c3_face_x, 1, C3_USB_WIDTH, C3_USB_HEIGHT, c3_usb_z)
c3_glass = box(glass_x0, glass_x1, -C3_GLASS_WIDTH / 2.0, C3_GLASS_WIDTH / 2.0, glass_front, c3_face)
c3_lit = box(screen_x - C3_SCREEN_HEIGHT / 2.0, screen_x + C3_SCREEN_HEIGHT / 2.0,
             screen_y - C3_SCREEN_WIDTH / 2.0, screen_y + C3_SCREEN_WIDTH / 2.0,
             glass_front - 0.02, glass_front)
buttons = union_all([box(button_x - 1.7, button_x + 1.7, y - 2.2, y + 2.2, button_front, c3_face)
                     for y in (boot_y, rst_y)])

c3_board = union_all([c3_pcb, c3_under, c3_usb, c3_glass, buttons])
charger = union_all([tp_pcb, tp_usb, tp_parts])

screw = union_all([
    cylinder_z(1.5, head_depth, screw_tip, post_x, post_y),
    cylinder_z(SCREW_HEAD_DIAMETER / 2.0, head_depth - WASHER_THICKNESS - SCREW_HEAD_HEIGHT,
               head_depth - WASHER_THICKNESS, post_x, post_y),
])
washer = (cylinder_z(WASHER_DIAMETER / 2.0, head_depth - WASHER_THICKNESS, head_depth, post_x, post_y)
          .cut(cylinder_z(1.6, -10, 50, post_x, post_y)))
nut = (hex_z(NUT_FLATS, nut_z0, nut_z0 + NUT_THICKNESS, post_x, post_y)
       .cut(cylinder_z(1.5, -10, 50, post_x, post_y)))
hardware = union_all([screw, washer, nut])


# ============================================================
# FRONT (TUB)
# ============================================================

label_spots = {}


def make_tub():

    # The walls go on past the lid as rails; the ends are cut down to
    # the smallest bottle's curve further on.
    tub = (box(outer_x0, outer_x1, -outer_half, outer_half, 0.0, rail_top)
           .edges("|Z").fillet(CORNER_RADIUS)
           .edges("<Z").chamfer(0.4))

    # Strap ears at the front face, flat on the bed.
    for x in ear_xs:
        for sign in (1.0, -1.0):
            y_wall = sign * (outer_half - 1.0)
            y_tip = sign * (outer_half + ear_reach)
            ear = (box(x - ear_hx, x + ear_hx, min(y_wall, y_tip), max(y_wall, y_tip),
                       0.0, EAR_THICKNESS)
                   .edges("|Z").fillet(min(2.0, ear_reach - 0.1)))
            tub = tub.union(ear)
            y0 = sign * (outer_half + 0.6)
            y1 = sign * (outer_half + 0.6 + STRAP_SLOT)
            tub = tub.cut(box(x - STRAP_WIDTH / 2.0 - 0.3, x + STRAP_WIDTH / 2.0 + 0.3,
                              min(y0, y1), max(y0, y1), -1.0, EAR_THICKNESS + 1.0)
                          .edges("|Z").fillet(min(1.0, STRAP_SLOT / 2.0 - 0.05)))

    tub = tub.cut(box(0.0, inner_length, -inner_half, inner_half, FLOOR, lid_z0 + 0.01))
    tub = tub.cut(box(0.0, pocket_x1, -rail_in, rail_in, lid_z0, big))   # lid pocket

    # Lips over the lid's bottom edge at the PRG end; the bottle cut below
    # trims them back to where they clear the bottle.
    tub = tub.union(box(-0.1, LIP, -rail_in - 0.1, rail_in + 0.1,
                        lid_z1 + 0.1, lid_z1 + 0.1 + LIP_THICKNESS))

    # Ribs along the long walls holding the C3's screen side off the front.
    reach = CLEARANCE + LEDGE
    for sign in (1.0, -1.0):
        y_in = sign * (inner_half - reach)
        y_out = sign * (inner_half + 0.1)
        tub = tub.union(box(max(c3_x0, 0.0), c3_x1, min(y_in, y_out), max(y_in, y_out),
                            FLOOR - 0.1, c3_face))

    # Screw post with a counterbore for the head and washer.
    tub = tub.union(cylinder_z(boss_r, FLOOR - 0.1, post_z1, post_x, post_y))
    tub = tub.cut(cylinder_z((WASHER_DIAMETER + HEAD_CLEARANCE) / 2.0, -0.1, head_depth,
                             post_x, post_y))
    tub = tub.cut(cylinder_z(SCREW_HOLE / 2.0, -0.1, post_z1 + 0.1, post_x, post_y))

    # Bezel inside the front round the window, up to just short of the glass.
    if bezel_z1 > FLOOR:
        tub = tub.union(box(screen_x - bezel_hx, screen_x + bezel_hx,
                            screen_y - bezel_hy, screen_y + bezel_hy, FLOOR - 0.1, bezel_z1))

    # Window, straight through, bevelled on the outside.
    tub = tub.cut(box(screen_x - window_hx, screen_x + window_hx,
                      screen_y - window_hy, screen_y + window_hy, -0.1, bezel_z1 + 0.1))
    c = WINDOW_CHAMFER
    tub = tub.cut(cq.Workplane("XY").workplane(offset=-0.2).center(screen_x, screen_y)
                  .rect(2 * (window_hx + c + 0.2), 2 * (window_hy + c + 0.2))
                  .workplane(offset=c + 0.2)
                  .rect(2 * window_hx, 2 * window_hy)
                  .loft())

    # BOOT flexure: U-shaped slot, tab thinned from inside, nub behind it.
    s = FLEX_SLOT
    tub = tub.cut(box(flex_x0, flex_x1 + s, boot_y - flex_hy - s, boot_y + flex_hy + s,
                      -0.1, FLOOR + 1.0))
    tub = tub.union(box(flex_x0 - 0.01, flex_x1, boot_y - flex_hy, boot_y + flex_hy,
                        0.0, FLEX_THICKNESS))
    tub = tub.union(cylinder_z(NUB_DIAMETER / 2.0, FLEX_THICKNESS - 0.01,
                               button_front - NUB_GAP, button_x, boot_y))

    # RST pin hole.
    tub = tub.cut(cylinder_z(RST_HOLE / 2.0, -0.1, FLOOR + 1.0, button_x, rst_y))

    # USB-C openings in the end walls.
    h, w = port_h["PRG"], port_w["PRG"]
    tub = tub.cut(box(outer_x0 - 1.0, 1.0, -w / 2.0, w / 2.0, c3_usb_z - h / 2.0, c3_usb_z + h / 2.0)
                  .edges("|X").fillet(min(1.2, h / 2.0 - 0.05)))
    h, w = port_h["PWR"], port_w["PWR"]
    tub = tub.cut(box(inner_length - 1.0, outer_x1 + 1.0, -w / 2.0, w / 2.0,
                      tp_usb_z - h / 2.0, tp_usb_z + h / 2.0)
                  .edges("|X").fillet(min(1.2, h / 2.0 - 0.05)))

    # Labels engraved in the front, reading upright with the PRG end down.
    label_spots["PRG"] = (screen_x - window_hx - WINDOW_CHAMFER - 1.0 - LABEL_SIZE / 2.0, 0.0)
    label_spots["PWR"] = (outer_x1 - CORNER_RADIUS - 1.0 - LABEL_SIZE / 2.0, 0.0)
    for name, (x, y) in label_spots.items():
        plane = cq.Plane(origin=(x, y, -0.2), xDir=(0, 1, 0), normal=(0, 0, -1))
        text = cq.Workplane(plane).text(name, LABEL_SIZE, -(LABEL_DEPTH + 0.2),
                                        font=LABEL_FONT, kind="bold",
                                        halign="center", valign="center")
        bb = text.val().BoundingBox()
        if bb.xmin < outer_x0 + 1.0 or bb.ymin < -outer_half + 1.5:
            error(f"label {name} runs off the front; make LABEL_SIZE smaller")
        tub = tub.cut(text)

    # Let the smallest bottle in: this curves the end walls' tops down
    # and leaves the side walls' inner edges as the rails.
    tub = tub.cut(bottle(BOTTLE_MIN_DIAMETER, gap=0.0))

    return tub


# ============================================================
# BACK (LID)
# ============================================================

def make_lid():

    # A flat plate in the pocket at the top of the walls: it prints flat
    # on its back, nothing hanging in the air.
    lid = box(lid_x0, lid_x1, -rail_in + 0.15, rail_in - 0.15, lid_z0, lid_z1)

    # Pegs pressing the C3 onto its ribs (clear of the wire pads at the
    # USB end).
    for x in (c3_x0 + 0.5 * C3_LENGTH, c3_x0 + 0.84 * C3_LENGTH):
        for sign in (1.0, -1.0):
            y = sign * (C3_WIDTH / 2.0 - PEG / 2.0 - 0.1)
            lid = lid.union(box(x - PEG / 2.0, x + PEG / 2.0, y - PEG / 2.0, y + PEG / 2.0,
                                c3_back, lid_z0 + 0.01))

    # Nut boss: hex pocket open at the back, clearance hole towards the front.
    lid = lid.union(cylinder_z(boss_r, boss_z0, lid_z0 + 0.01, post_x, post_y))
    lid = lid.cut(hex_z(NUT_FLATS + NUT_FIT, nut_z0, lid_z1 + 1.0, post_x, post_y))
    lid = lid.cut(cylinder_z(SCREW_HOLE / 2.0, boss_z0 - 0.1, nut_z0 + 0.01, post_x, post_y))

    return lid


big = 200.0

print("Building front ...")
tub = make_tub()
base = tub                                    # fit_test.py and the STL name use "base"
print("Building back ...")
lid = make_lid()


# ============================================================
# FIT CHECK
# ============================================================

if CHECK_FIT:
    print("Checking fit ...")
    parts = {"battery": battery, "charger": charger, "C3 board": c3_board,
             "screw": screw, "washer": washer, "nut": nut}
    tests = []
    for name, shape in parts.items():
        tests.append((f"{name} hits the front", shape, tub))
        tests.append((f"{name} hits the back", shape, lid))
    tests += [
        ("battery hits the charger", battery, charger),
        ("battery hits the C3 board", battery, c3_board),
        ("front hits the back", tub, lid),
    ]
    for d in (BOTTLE_MIN_DIAMETER, BOTTLE_MAX_DIAMETER):
        tests.append((f"{d:g} mm bottle hits the back", bottle(d), lid))
        tests.append((f"{d:g} mm bottle hits the front", bottle(d), tub))
    clashes = []
    for name, a, b in tests:
        overlap = volume(a.intersect(b))
        if overlap > 0.01:
            clashes.append(f"{name} ({overlap:.2f} mm3)")
    for clash in clashes:
        print(f"WARNING: overlap - {clash}")
    if not clashes:
        print("  no overlaps")


# ============================================================
# EXPORT (print orientation)
# ============================================================

def lid_printed():
    return to_bed(lid.rotate((0, 0, 0), (1, 0, 0), 180))  # rails on the bed


if __name__ == "__main__":

    print_parts = {"base": tub, "lid": lid_printed()}
    written = []
    for name, shape in print_parts.items():
        filename = HERE / f"{OUTPUT_PREFIX}_{name}.stl"
        cq.exporters.export(shape, str(filename),
                            tolerance=STL_TOLERANCE, angularTolerance=STL_ANGULAR_TOLERANCE)
        written.append(filename.name)


# ============================================================
# PREVIEW IMAGE
# ============================================================

COLORS = {
    "base": (0.20, 0.55, 0.62),
    "lid": (0.35, 0.70, 0.78),
    "battery": (0.78, 0.78, 0.80),
    "charger": (0.15, 0.18, 0.22),
    "c3": (0.45, 0.25, 0.60),
    "usb": (0.85, 0.85, 0.88),
    "glass": (0.08, 0.08, 0.10),
    "lit": (0.95, 0.95, 0.95),
    "screw": (0.30, 0.30, 0.32),
    "bottle": (0.93, 0.55, 0.45),
}


def mesh(shape, color):

    import numpy as np

    vertices, triangles = cq.Compound.makeCompound(shape.vals()).tessellate(0.05, 0.2)
    if not triangles:
        return np.zeros((0, 3, 3)), np.zeros((0, 3))
    xyz = np.array([(v.x, v.y, v.z) for v in vertices])
    tris = xyz[np.array(triangles, dtype=int)]

    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    normals = normals / np.where(lengths == 0.0, 1.0, lengths)[:, None]

    light = np.array([-0.5, -0.6, -0.65])
    light = light / np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.abs(normals @ light)
    return tris, shade[:, None] * np.array(color)


def front_drawing(ax, title):
    """The front, drawn flat from the model's numbers, bar upright."""

    import matplotlib.patches as patches

    # Plot Y across (right) and X up, as seen from the front.
    def rect(x0, x1, y0, y1, color, z, round_=0.0, label=None, edge="0.2"):
        ax.add_patch(patches.FancyBboxPatch(
            (y0, x0), y1 - y0, x1 - x0, boxstyle=f"round,pad=0,rounding_size={round_}",
            facecolor=color, edgecolor=edge, linewidth=0.6, zorder=z, label=label))

    for x in ear_xs:
        for sign in (1.0, -1.0):
            y_tip = sign * (outer_half + ear_reach)
            rect(x - ear_hx, x + ear_hx, min(0.0, y_tip), max(0.0, y_tip), COLORS["base"], 1, 2.0)
            y0, y1 = sign * (outer_half + 0.6), sign * (outer_half + 0.6 + STRAP_SLOT)
            rect(x - STRAP_WIDTH / 2.0 - 0.3, x + STRAP_WIDTH / 2.0 + 0.3, min(y0, y1), max(y0, y1),
                 "white", 3, 1.0)
    rect(outer_x0, outer_x1, -outer_half, outer_half, COLORS["base"], 2, CORNER_RADIUS)
    rect(screen_x - window_hx, screen_x + window_hx, screen_y - window_hy, screen_y + window_hy,
         "0.05", 4, label="window")
    ax.add_patch(patches.Rectangle((screen_y - C3_SCREEN_WIDTH / 2.0, screen_x - C3_SCREEN_HEIGHT / 2.0),
                                   C3_SCREEN_WIDTH, C3_SCREEN_HEIGHT, facecolor="0.85", zorder=5))
    s = FLEX_SLOT
    rect(flex_x0, flex_x1 + s, boot_y - flex_hy - s, boot_y + flex_hy + s, "white", 4)
    rect(flex_x0, flex_x1, boot_y - flex_hy, boot_y + flex_hy, COLORS["lid"], 5, label="BOOT tab")
    ax.add_patch(patches.Circle((rst_y, button_x), RST_HOLE / 2.0, color="0.05", zorder=5))
    ax.add_patch(patches.Circle((post_y, post_x), (WASHER_DIAMETER + HEAD_CLEARANCE) / 2.0,
                                facecolor=COLORS["screw"], zorder=5, label="screw"))
    for name, (x, y) in label_spots.items():
        ax.text(y, x, name, ha="center", va="center", fontsize=8, fontweight="bold",
                color="0.95", zorder=6)
    ax.text(0, outer_x0 - 4.0, "PRG port (bottom)", ha="center", fontsize=7)
    ax.text(0, outer_x1 + 2.0, "PWR port (top)", ha="center", fontsize=7)
    ax.set_xlim(-outer_half - ear_reach - 3.0, outer_half + ear_reach + 3.0)
    ax.set_ylim(outer_x0 - 7.0, outer_x1 + 6.0)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.3)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, loc="lower right")
    ax.set_title(title, fontsize=10)


def render_preview(filename):

    import numpy as np
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    inside = [
        (battery, "battery"),
        (tp_pcb.union(tp_parts), "charger"), (tp_usb, "usb"),
        (c3_pcb.union(c3_under).union(buttons), "c3"), (c3_usb, "usb"),
        (c3_glass, "glass"), (c3_lit, "lit"),
    ]

    def shifted(items, dz):
        return [(shape.translate((0, 0, dz)), color) for shape, color in items]

    assembled = [(tub, "base"), (lid, "lid"), (hardware, "screw")]
    exploded = ([(screw.union(washer).translate((0, 0, -14.0)), "screw"), (tub, "base")]
                + shifted(inside, 10.0)
                + [(lid.translate((0, 0, 22.0)), "lid"), (nut.translate((0, 0, 34.0)), "screw")])
    on_bottle = [(tub, "base"), (lid, "lid"),
                 (bottle(BOTTLE_MIN_DIAMETER + 2.0).intersect(
                     box(outer_x0 - 15, outer_x1 + 15, -big, big, -big, big)), "bottle")]

    keep = box(-big, big, -big, 0.0, -big, big)
    section = [(shape.intersect(keep), color)
               for shape, color in [(tub, "base"), (lid, "lid"), (hardware, "screw")] + inside]

    views = [
        ("Front (mm), PRG end down", None, 0, 0),
        ("Assembled, from the front", assembled + [(c3_lit, "lit")], -60, -120),
        ("Exploded (front at the bottom)", exploded, 20, -120),
        ("On a 70 mm bottle, seen from above", on_bottle, 0, 0),
        ("Section on the centre line", section, 0, 90),
        ("Back: rails and nut pocket", [(tub, "base"), (lid, "lid")], 55, -120),
    ]

    fig = plt.figure(figsize=(15, 10))

    for index, (title, items, elevation, azimuth) in enumerate(views):
        if items is None:
            front_drawing(fig.add_subplot(2, 3, index + 1), title)
            continue
        ax = fig.add_subplot(2, 3, index + 1, projection="3d")
        all_tris, all_colors = [], []
        for shape, color_name in items:
            if not shape.vals():
                continue
            tris, colors = mesh(shape, COLORS[color_name])
            all_tris.append(tris)
            all_colors.append(colors)
        tris = np.concatenate(all_tris)
        colors = np.concatenate(all_colors)
        ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolors="none"))

        lo = tris.reshape(-1, 3).min(axis=0)
        hi = tris.reshape(-1, 3).max(axis=0)
        centre = (lo + hi) / 2.0
        half = (hi - lo).max() / 2.0 + 1.0
        ax.set_xlim(centre[0] - half, centre[0] + half)
        ax.set_ylim(centre[1] - half, centre[1] + half)
        ax.set_zlim(centre[2] - half, centre[2] + half)
        ax.set_box_aspect((1, 1, 1))
        ax.set_proj_type("ortho")
        ax.view_init(elev=elevation, azim=azimuth)
        ax.set_axis_off()
        ax.set_title(title, fontsize=10)

    fig.suptitle(
        f"c3-pal bottle bar - {outer_x1 - outer_x0:.1f} long x {2 * outer_half:.1f} wide "
        f"({2 * (outer_half + ear_reach):.1f} at the strap ears) x {rail_top:.1f} thick, "
        f"1x M3x{screw_length} + nut + washer",
        fontsize=12)
    fig.tight_layout()
    fig.savefig(HERE / filename, dpi=130)


if __name__ == "__main__" and PREVIEW:
    print("Rendering preview ...")
    try:
        render_preview(PREVIEW_FILE)
        written.append(PREVIEW_FILE)
    except ImportError:
        print("Preview skipped (python -m pip install matplotlib)")
    except Exception as exc:
        print(f"WARNING: Preview failed: {exc}")


# ============================================================
# FINAL REPORT
# ============================================================

if __name__ == "__main__":

    grams = (volume(tub) + volume(lid)) / 1000.0 * PLA_DENSITY

    print()
    print("=============================================================")
    print("FINISHED WITH ERRORS" if errors else "SUCCESS")
    print("=============================================================")
    print()
    print("Generated:")
    for name in written:
        print(f"  {name}")
    print()
    print("Geometry:")
    print(f"  Bar:       {outer_x1 - outer_x0:.1f} long, {2 * outer_half:.1f} wide "
          f"({2 * (outer_half + ear_reach):.1f} at the ears), {rail_top:.1f} thick "
          f"(side walls stand {rail_h:.1f} past the back as rails)")
    print(f"  Depth:     front {FLOOR:g}, battery {batt_z0:.1f}-{batt_z1:.1f}, "
          f"C3 PCB {c3_face:.1f}-{c3_back:.1f} (face down), back {lid_z0:.1f}-{lid_z1:.1f}")
    print(f"  Along:     C3 {c3_x0:.1f}-{c3_x1:.1f}, battery {batt_x0:.1f}-{batt_x1:.1f}, "
          f"screw {post_x:.1f}, TP4056 {tp_x0:.1f}-{tp_x1:.1f}")
    print(f"  Window:    {2 * window_hy:.1f} x {2 * window_hx:.1f}, "
          f"{bezel_z1:.1f} deep, {glass_front - bezel_z1:.1f} short of the glass")
    print(f"  Straps:    2x up to {STRAP_WIDTH:g} wide, slots {STRAP_SLOT:g}; "
          f"bottles {BOTTLE_MIN_DIAMETER:g}-{BOTTLE_MAX_DIAMETER:g} across")
    print(f"  Screw:     1x M3x{screw_length} + washer from the front, nut in the back "
          f"({screw_tip - nut_z0 - NUT_THICKNESS:.1f} past the nut)")
    print(f"  Weight:    {grams:.0f} g solid PLA (less with infill)")
    print()
    print("Print: front face down, back on its back face; no supports.")
    print("=============================================================")
    if errors:
        sys.exit(1)
