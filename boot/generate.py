"""
c3-pal boot generator
=====================

Units: millimetres

A TPU boot for the bottom of an Owala FreeSip Sway (as in the owala boots
project) that carries the c3-pal hydration buddy and an Apple AirTag:

    boot     TPU 90A cup the bottle pushes down into; the inside is a
             little smaller than the bottle (FIT_SQUEEZE) so it grips.
             In its floor: the AirTag pocket at the back (lip, push
             hole, sound holes, spring bumps, as on the owala boot) and
             the pod pocket at the front.  At the front a TPU frame
             wraps the pod's tower and reaches over the edges of its
             face.
    pod      PETG.  A tray under the bottle for the LP702030 battery
             and the TP4056 charger, and at the front a tower that
             stands up outside the bottle for the C3 board, screen out:
             window, BOOT tab and RST hole in its face, PWR (TP4056
             USB-C) at the bottom of the face, PRG (C3 USB-C) out of
             its top.
    lid      PETG L: a plate over the tray, which the bottle stands on,
             and a wall closing the tower on the bottle side.  It goes
             straight down: the wall drops into grooves in the tower's
             side walls (full height, so the buttons' push is taken by
             the tower) and closes the tower's top.  Two clips on the
             tray's sides snap over a step in its edge, and two M3
             socket head screws come up through two columns beside the
             battery (heads in counterbores underneath) into hex nuts
             pressed into its top.

Requires:
    CadQuery, matplotlib (preview only)

Run:
    python generate.py

Output (in this folder):
    c3pal_boot.stl        boot (TPU), floor on the bed
    c3pal_pod.stl         pod (PETG), floor on the bed
    c3pal_pod_lid.stl     lid (PETG), plate on the bed, wall up
    c3pal_boot_preview.png

Coordinates (as fitted, bottle upright):
    Z  up the bottle's axis; z = 0 the bottom of the boot (its bed)
    X  out from the axis towards the tower (the front, where the screen
       faces)
    Y  across, +Y to the right seen from the front

Assembly:
    1. Solder: battery -> TP4056 B+/B-; TP4056 OUT+ -> diode -> C3 5V,
       OUT- -> C3 GND.
    2. TP4056 into the pod, parts up, USB-C into the PWR opening; battery
       on the floor behind it (tape both).
    3. C3 into the tower from the bottle side, screen out, USB-C up into
       the PRG slot, bottom edge on the two posts: push it in until it
       snaps past the lips on the tower's side walls.
    4. Press the two M3 hex nuts into the pockets in the lid's top.
       Lid: wall into the grooves in the tower's side walls, push it
       straight down until the clips snap over the plate's edge.  M3x8
       socket head screws up through the columns from under the pod
       into the nuts (gently).
    5. AirTag into its pocket, white side up, past the lip.
    6. Pod into the boot: straight down, the tower sliding down into the
       frame behind its lips and the strap across the face, and in under
       the boot's wall over the tower (the back strap; stretch it).
       Press the tray down.  Push the bottle in.
"""

import json
import math
import sys
import time
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


# Bottle
BASE_DIAMETER = param("BASE_DIAMETER")
UPPER_DIAMETER = param("UPPER_DIAMETER")
UPPER_HEIGHT = param("UPPER_HEIGHT")
CORNER_RADIUS = param("CORNER_RADIUS")

# Boot
WALL = param("WALL")
WALL_HEIGHT = param("WALL_HEIGHT")
FIT_SQUEEZE = param("FIT_SQUEEZE")
FLOOR_UNDER = param("FLOOR_UNDER")
BOTTOM_ROUND = param("BOTTOM_ROUND")
TOP_ROUND = param("TOP_ROUND")
DRAIN_HOLES = param("DRAIN_HOLES")
DRAIN_DIAMETER = param("DRAIN_DIAMETER")
FRAME = param("FRAME")
FRAME_LIP = param("FRAME_LIP")
FRAME_FRONT = param("FRAME_FRONT")
POD_FIT = param("POD_FIT")
STRAP = param("STRAP")
STRAP_GAP = param("STRAP_GAP")
BACK_STRAP = param("BACK_STRAP")

# AirTag
AIRTAG_DIAMETER = param("AIRTAG_DIAMETER")
AIRTAG_THICKNESS = param("AIRTAG_THICKNESS")
AIRTAG_CLEARANCE = param("AIRTAG_CLEARANCE")
AIRTAG_HEADROOM = param("AIRTAG_HEADROOM")
LIP = param("LIP")
LIP_HEIGHT = param("LIP_HEIGHT")
PUSH_HOLE_DIAMETER = param("PUSH_HOLE_DIAMETER")
SOUND_HOLES = param("SOUND_HOLES")
SOUND_HOLE_DIAMETER = param("SOUND_HOLE_DIAMETER")
SPRING_BUMPS = param("SPRING_BUMPS")
SPRING_HEIGHT = param("SPRING_HEIGHT")
SPRING_DIAMETER = param("SPRING_DIAMETER")
AIRTAG_EDGE = param("AIRTAG_EDGE")

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

# Pod
POD_WALL = param("POD_WALL")
POD_FLOOR = param("POD_FLOOR")
FACE = param("FACE")
TOWER_WALL = param("TOWER_WALL")
GROOVE = param("GROOVE")
KEEPER = param("KEEPER")
PORT_WALL = param("PORT_WALL")
LID = param("LID")
PLATE = param("PLATE")
LID_GAP = param("LID_GAP")
CLEARANCE = param("CLEARANCE")
FRONT_GAP = param("FRONT_GAP")
BACK_GAP = param("BACK_GAP")
WIRE_GAP = param("WIRE_GAP")
LEAD_GAP = param("LEAD_GAP")
BOARD_GAP = param("BOARD_GAP")
PORT_INSET = param("PORT_INSET")
PORT_CLEARANCE = param("PORT_CLEARANCE")
LEDGE = param("LEDGE")
PEG = param("PEG")
BOARD_LIP = param("BOARD_LIP")
BOARD_LIP_HEIGHT = param("BOARD_LIP_HEIGHT")
LIP_SLOT = param("LIP_SLOT")
TAB_GAP = param("TAB_GAP")

# Fasteners
SCREW_HOLE = param("SCREW_HOLE")
HEAD_DIAMETER = param("HEAD_DIAMETER")
HEAD_HEIGHT = param("HEAD_HEIGHT")
SCREW_LENGTH = param("SCREW_LENGTH")
NUT_WIDTH = param("NUT_WIDTH")
NUT_THICKNESS = param("NUT_THICKNESS")
NUT_FIT = param("NUT_FIT")
NUT_RECESS = param("NUT_RECESS")
NUT_FLOOR = param("NUT_FLOOR")
BOSS_WALL = param("BOSS_WALL")
CLIP_WIDTH = param("CLIP_WIDTH")
CLIP_THICKNESS = param("CLIP_THICKNESS")
CLIP_SLOT = param("CLIP_SLOT")
CLIP_HOOK = param("CLIP_HOOK")
CLIP_ROOT = param("CLIP_ROOT")

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

# Labels
LABEL_SIZE = param("LABEL_SIZE")
LABEL_DEPTH = param("LABEL_DEPTH")
LABEL_FONT = param("LABEL_FONT")

# Plugs
PLUG_WIDTH = param("PLUG_WIDTH")
PLUG_THICKNESS = param("PLUG_THICKNESS")
PLUG_LENGTH = param("PLUG_LENGTH")

# Output
PREVIEW = param("PREVIEW")
CHECK_FIT = param("CHECK_FIT")
TPU_DENSITY = param("TPU_DENSITY")
PETG_DENSITY = param("PETG_DENSITY")

if _params:
    sys.exit(f"{PARAMS_FILE}: unknown parameter(s): {', '.join(sorted(_params))}")

if C3_BOOT_SIDE not in ("left", "right"):
    sys.exit(f"C3_BOOT_SIDE must be 'left' or 'right', not '{C3_BOOT_SIDE}'")

PREVIEW_FILE = f"{OUTPUT_PREFIX}_boot_preview.png"
# The boot's round wall: fine, so it prints round (owala boots, 2026-11-06).
BOOT_TOLERANCE = 0.005
BOOT_ANGULAR_TOLERANCE = 0.02
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.1

errors = []


T0 = time.time()


def stage(name):
    print(f"{name} ... ({time.time() - T0:.0f} s)", flush=True)


def error(message):
    errors.append(message)
    print(f"ERROR: {message}")


# ============================================================
# LAYOUT
# ============================================================

# Half section through the middle (Y = 0), front to the right:
#
#                     bottle                    ┃▓┃ PRG (C3 USB-C up)
#        │                                │     ┃C┃
#        │                                │lid ▕┃3┃▏ face: window,
#  wall █│                                │wall▕┃ ┃▏ BOOT tab, RST
#       █ ╲______________________________╱    ▕┃ ┃▏
#   ████ ▄▄▄lip▄▄▄  ███ ═══ lid plate ═══════ ▕   ▏
#   ███   AirTag  █ ███ battery  ▯ TP4056 ═══ ▕ ▭ ▏ PWR (TP4056 USB-C)
#   ███▀▀  ▀▀  ▀▀▀███████████ TPU floor █████████▏
#
#        AirTag pocket (TPU)   pod tray (PETG)   tower (PETG) in the
#                                                TPU frame

c = FIT_SQUEEZE / 2.0

# Bottle: its side is a straight line through BASE_DIAMETER (taken at
# CORNER_RADIUS above its bottom) and UPPER_DIAMETER at UPPER_HEIGHT.
base_radius = BASE_DIAMETER / 2.0
taper = (UPPER_DIAMETER - BASE_DIAMETER) / 2.0 / (UPPER_HEIGHT - CORNER_RADIUS)


def bottle_radius(height):
    """Radius of the bottle's side, height above its bottom."""

    return base_radius + taper * (height - CORNER_RADIUS)


bottle_flat = base_radius - CORNER_RADIUS

# --- up (Z) ---
pod_z0 = FLOOR_UNDER                          # pod's underside, on the TPU floor
pod_in = pod_z0 + POD_FLOOR                   # top of the pod's floor
batt_z0 = pod_in
batt_z1 = batt_z0 + BATT_THICKNESS
tp_z0 = pod_in                                # PCB on the floor, parts up
tp_top = tp_z0 + TP_PCB
tp_usb_z = tp_top + TP_USB_HEIGHT / 2.0
tp_z1 = tp_top + max(TP_USB_HEIGHT, TP_PARTS)

lid_z0 = max(batt_z1 + WIRE_GAP, tp_z1 + 0.3)
lid_z1 = lid_z0 + PLATE
floor_top = lid_z1                            # the bottle stands on the lid and the TPU round it

# C3 upright, buttons at the bottom, USB-C at the top, over the TP4056's
# USB-C.
c3_z0 = tp_top + TP_USB_HEIGHT + BOARD_GAP    # PCB's bottom (button) edge
c3_z1 = c3_z0 + C3_LENGTH                     # PCB's top (USB) edge
c3_usb_top = c3_z1 + C3_USB_OVERHANG          # receptacle face
tower_in = c3_usb_top - PORT_INSET            # underside of the tower's top
tower_top = tower_in + PORT_WALL

top_z = floor_top + WALL_HEIGHT

# --- out (X) ---
# The lid's wall faces the bottle: flat, LID_GAP off it where the bottle
# is widest (the tower's top).
wall_x0 = bottle_radius(tower_top - floor_top) + LID_GAP
wall_x1 = wall_x0 + LID
groove_x0 = wall_x0 - 0.15                    # grooves in the tower's side walls for the lid's wall
groove_x1 = wall_x1 + 0.15
tower_x0 = groove_x0 - KEEPER                 # back of the tower's side walls (behind the grooves)
c3_back = wall_x1 + BACK_GAP + C3_UNDER       # PCB's underside
c3_face = c3_back + C3_PCB                    # component side (screen, buttons, USB-C)
c3_usb_x = c3_face + C3_USB_HEIGHT / 2.0
face_in = c3_face + C3_USB_HEIGHT + FRONT_GAP
face_x = face_in + FACE                       # outside of the face
glass_front = c3_face + C3_OLED_HEIGHT
button_front = c3_face + C3_BUTTON_HEIGHT

tp_face_x = face_in + PORT_INSET              # TP4056 receptacle face
tp_x1 = tp_face_x - TP_USB_OVERHANG
tp_x0 = tp_x1 - TP_LENGTH
batt_x1 = tp_x0 - LEAD_GAP
batt_x0 = batt_x1 - BATT_WIDTH
tray_in_x0 = batt_x0 - CLEARANCE
tray_x0 = tray_in_x0 - POD_WALL
batt_zone_x1 = batt_x1 + CLEARANCE + POD_WALL

# --- across (Y) ---
tower_in_half = C3_WIDTH / 2.0 + CLEARANCE
tower_half = tower_in_half + TOWER_WALL
groove_half = tower_in_half + GROOVE
lid_wall_half = groove_half - 0.15
batt_in_half = BATT_LENGTH / 2.0 + CLEARANCE
batt_half = batt_in_half + POD_WALL
rib_in = tower_in_half - CLEARANCE - LEDGE    # ribs and posts under the C3's edges

frame_half = tower_half + FRAME
opening_half = tower_half - FRAME_LIP         # the frame's opening over the face

# --- the lid's pegs on the C3's back, and the board lips between them ---
peg_zs = [c3_z1 - 0.5 * C3_LENGTH, c3_z1 - 0.84 * C3_LENGTH]     # bottoms
lip_zs = [c3_z0 + 0.63 * C3_LENGTH - BOARD_LIP_HEIGHT / 2.0,      # bottoms
          c3_z1 - 2.0 - BOARD_LIP_HEIGHT]
lip_tip = C3_WIDTH / 2.0 - BOARD_LIP                              # |y| of the lip's tip
lip_depth = tower_in_half - lip_tip                               # out from the wall
lip_x1 = c3_back - 0.05                                           # face on the board's back
lip_x0 = lip_x1 - lip_depth                                       # 45 degree lead-in
tongue_x1 = c3_face - 0.2                                         # tongue: groove_x1 to here
tongue_z0 = lid_z1 + 1.0                                          # hinge
tongue_z1 = max(lip_zs) + BOARD_LIP_HEIGHT + 0.5

# --- C3 features (the board is upside down: USB-C up) ---
boot_sign = -1.0 if C3_BOOT_SIDE == "right" else 1.0
boot_y = boot_sign * (C3_WIDTH / 2.0 - C3_BUTTON_FROM_SIDE)
rst_y = -boot_y
button_z = c3_z0 + C3_BUTTON_FROM_END

screen_z = c3_z0 + C3_SCREEN_FROM_END
screen_y = C3_SCREEN_OFFSET
window_hz = C3_SCREEN_HEIGHT / 2.0 + WINDOW_MARGIN
window_hy = C3_SCREEN_WIDTH / 2.0 + WINDOW_MARGIN
bezel_hz = window_hz + BEZEL_MARGIN
bezel_hy = window_hy + BEZEL_MARGIN
bezel_x0 = min(glass_front + BEZEL_GAP, face_in)
glass_z0 = c3_z0 + C3_GLASS_FROM_END
glass_z1 = glass_z0 + C3_GLASS_LENGTH

# BOOT flexure: hinged at the bottom so it prints growing up from the
# hinge (hinged at the top, its free end was floating), free end up
# just past the button.
flex_z1 = button_z + NUB_DIAMETER / 2.0 + 1.0
flex_z0 = flex_z1 - FLEX_LENGTH
flex_hy = FLEX_WIDTH / 2.0
s = FLEX_SLOT

# --- ports ---
prg_w = C3_USB_WIDTH + PORT_CLEARANCE
prg_t = C3_USB_HEIGHT + PORT_CLEARANCE
pwr_w = TP_USB_WIDTH + PORT_CLEARANCE
pwr_h = TP_USB_HEIGHT + PORT_CLEARANCE

# The PWR opening sits under the BOOT tab; move it (and the TP4056)
# across, away from the tab, until it clears the tab's slot.
pwr_y = 0.0
if tp_usb_z + pwr_h / 2.0 > flex_z0 - TAB_GAP:
    need = pwr_w / 2.0 + TAB_GAP - (abs(boot_y) - flex_hy - s)
    pwr_y = -boot_sign * max(0.0, need)
tp_y = pwr_y - TP_USB_OFFSET                  # board centre

# --- AirTag pocket, as far back as the outside allows ---
pocket_radius = (AIRTAG_DIAMETER + AIRTAG_CLEARANCE) / 2.0
pocket_top = floor_top - LIP_HEIGHT           # under the lip
pocket_floor = pocket_top - AIRTAG_HEADROOM - AIRTAG_THICKNESS
lip_radius = pocket_radius - LIP
push_radius = PUSH_HOLE_DIAMETER / 2.0
sound_radius = SOUND_HOLE_DIAMETER / 2.0
sound_ring = (push_radius + pocket_radius) / 2.0
spring_radius = SPRING_DIAMETER / 2.0
spring_ring = (push_radius + sound_ring - sound_radius) / 2.0


def inner_radius(z):
    return bottle_radius(z - floor_top) - c


def outer_radius(z):
    return inner_radius(z) + WALL


outer_bottom = outer_radius(BOTTOM_ROUND)


def outside_at(z):
    """The boot's outside radius at height z, with the rounded bottom edge."""

    if z >= BOTTOM_ROUND:
        return outer_radius(z)
    dz = BOTTOM_ROUND - z
    return outer_bottom - BOTTOM_ROUND + math.sqrt(BOTTOM_ROUND ** 2 - dz ** 2)


airtag_x = -(outside_at(pocket_floor) - AIRTAG_EDGE - pocket_radius)
inner_flat = bottle_flat - c

# --- screws: socket head cap screws up from under the pod, heads in
# counterbores in two columns beside the battery, into hex nuts pressed
# into the lid plate's top (flush) ---
nut_hole_af = NUT_WIDTH + NUT_FIT
nut_hole_r = nut_hole_af / math.sqrt(3.0)     # to the pocket's corners
bore_r = HEAD_DIAMETER / 2.0 + 0.25           # counterbore for the head
boss_r = max(nut_hole_r, bore_r) + BOSS_WALL
screw_x = batt_x1 - boss_r - 1.0
screw_y = batt_in_half + boss_r               # the columns touch the battery's room
screw_spots = [(screw_x, sign * screw_y) for sign in (1.0, -1.0)]
nut_top = lid_z1 - NUT_RECESS
nut_z0 = nut_top - NUT_THICKNESS              # on the lid's floor under it
screw_tip = nut_top                           # the tip ends flush with the nut's top
head_top = screw_tip - SCREW_LENGTH           # the counterbore's top
head_z0 = head_top - HEAD_HEIGHT

# --- clips: arms on the tray's sides, hooks over a step in the lid's edge ---
clip_x0 = tray_x0 + 2.5                       # past the tray's rounded corner
clip_x1 = clip_x0 + CLIP_WIDTH
clip_y0 = batt_half + CLIP_SLOT               # arm's inside
clip_y1 = clip_y0 + CLIP_THICKNESS
hook_z = lid_z1 - CLIP_HOOK                   # hook's underside, on the lid's step
step_x0 = clip_x0 - 0.3                       # the step under the hook
step_x1 = clip_x1 + 0.3

# --- strap: TPU across the tower's face, joining the frame's sides ---
# The boot's wall is open where the tower goes through it, so the bottle
# stretching the boot pulls the frame's sides apart (they opened into a V
# on the first print). The strap closes the ring over the face above the
# window, from the frame's top down; its underside goes down 45 degrees
# each way from the middle (prints without support), STRAP_GAP over the
# screen's bezel. The pod slides down behind it as behind the lips.
strap_half = opening_half + 0.5                          # into the lips
strap_apex = screen_z + bezel_hz + STRAP_GAP + bezel_hy + abs(screen_y)


def strap_underside(y):
    return strap_apex - abs(y)


# Back strap: the boot's wall is kept whole over the tower's top, flat
# underneath (bridged over the tower), and in behind the PRG plug. The
# pod goes in from underneath it, stretching the TPU.
back_z0 = tower_top + 0.3
back_x1 = c3_usb_x - PLUG_THICKNESS / 2.0 - 0.3          # the wall stops short of the PRG plug

# --- sanity checks ---
if pocket_floor < 0.8:
    error("the floor under the AirTag is thinner than 0.8; the pod sets the floor's height")
if airtag_x + pocket_radius > tray_x0 + POD_FIT / 2.0 - AIRTAG_EDGE:
    error(f"the AirTag pocket (to x = {airtag_x + pocket_radius:.1f}) runs into the pod pocket "
          f"(from x = {tray_x0:.1f}); the floor is too small for both")
if abs(tp_y) + TP_WIDTH / 2.0 > rib_in - 0.2:
    error(f"the TP4056 (to y = {abs(tp_y) + TP_WIDTH / 2.0:.1f}) runs into the posts under the C3 "
          f"(from y = {rib_in:.1f}); it was moved {abs(pwr_y):.1f} across to clear the BOOT tab")
if abs(pwr_y) + pwr_w / 2.0 > opening_half:
    error("the PWR opening runs under the frame's lips")
if abs(rst_y) - RST_HOLE / 2.0 < abs(pwr_y) + pwr_w / 2.0 + 0.8 \
        and button_z - RST_HOLE / 2.0 < tp_usb_z + pwr_h / 2.0 + 0.8 and rst_y * pwr_y > 0:
    error("the RST hole runs into the PWR opening")
if flex_z1 + s > screen_z - bezel_hz - 0.4 and abs(boot_y) - flex_hy - s < abs(screen_y) + bezel_hy:
    error(f"BOOT flexure (top z = {flex_z1 + s:.1f}) runs into the screen bezel "
          f"(from z = {screen_z - bezel_hz:.1f}); shorten FLEX_LENGTH")
if abs(boot_y) + flex_hy + s > opening_half - 0.5:
    error("the BOOT tab is under the frame's lips")
if face_x - FLEX_THICKNESS - (button_front + NUB_GAP) < 0.3:
    error("the BOOT button is too close to the face for a nub")
if tower_top > top_z:
    error("the tower stands above the boot's wall; make WALL_HEIGHT bigger")
if batt_half > inner_flat + 4.0:
    error("the battery is too long for the floor")
for lz in lip_zs:
    if any(lz < pz + PEG + 0.5 and lz + BOARD_LIP_HEIGHT > pz - 0.5 for pz in peg_zs):
        error(f"a board lip (z = {lz:.1f}) runs into a lid peg")
if lip_x0 < groove_x1 + 0.1:
    error("the board lips start before their tongues (behind the grooves); make BOARD_LIP smaller")
if GROOVE > TOWER_WALL - 0.8:
    error("the grooves leave less than 0.8 of the tower's side walls")
if min(lip_zs) < tongue_z0 + 5.0:
    error("the lower board lip is too close to its tongue's hinge to flex")
if tongue_z1 + LIP_SLOT > tower_in - 1.0:
    error("the board lips' tongues reach the tower's top")
if nut_z0 - lid_z0 < NUT_FLOOR - 0.01:
    error(f"the lid plate is too thin for the nuts; PLATE must be at least "
          f"{NUT_FLOOR + NUT_THICKNESS + NUT_RECESS:.1f}")
if head_z0 < pod_z0:
    error(f"the screw heads stick out {pod_z0 - head_z0:.1f} under the pod; use shorter screws")
if lid_z0 - head_top < 2.0:
    error(f"only {lid_z0 - head_top:.1f} of column over the screw heads; use longer screws")
for sx, sy in screw_spots:
    if math.hypot(sx - airtag_x, sy) < pocket_radius + boss_r + AIRTAG_EDGE:
        error("a screw column runs into the AirTag pocket")
    if math.hypot(sx, sy) + boss_r > outside_at(pod_z0) - 2.0:
        error("a screw column comes too close to the boot's outside")
if step_x1 > screw_x - boss_r - 0.5:
    error("the clips run into the screw columns")
if hook_z - lid_z0 < 0.6:
    error("the lid's step under the clips is thinner than 0.6; make PLATE thicker")
if math.hypot(clip_x0 - airtag_x, clip_y1) < pocket_radius + AIRTAG_EDGE:
    error("a clip runs into the AirTag pocket")
if tower_top - strap_apex < 3.0:
    error(f"the strap over the face is only {tower_top - strap_apex:.1f} tall in the middle; "
          f"make STRAP_GAP smaller")
if top_z - back_z0 < BACK_STRAP - 0.01:
    error(f"only {top_z - back_z0:.1f} of wall over the tower (the back strap); WALL_HEIGHT must be at least "
          f"{back_z0 + BACK_STRAP - floor_top:.1f}")
if strap_underside(abs(boot_y) + flex_hy + s) < flex_z1 + s + 0.5:
    error("the strap over the face covers the BOOT tab")
if strap_underside(abs(rst_y) + RST_HOLE / 2.0) < button_z + RST_HOLE / 2.0 + 0.5:
    error("the strap over the face covers the RST hole")


# ============================================================
# HELPERS
# ============================================================

big = 400.0


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cylinder_z(radius, z0, z1, x=0.0, y=0.0):
    return (cq.Workplane("XY").circle(radius).extrude(z1 - z0)
            .translate((x, y, z0)))


def cylinder_x(radius, x0, x1, y=0.0, z=0.0):
    return (cq.Workplane("YZ").circle(radius).extrude(x1 - x0)
            .translate((x0, y, z)))


def prism_xz(points, y0, y1):
    """A closed (x, z) outline, extruded across from y0 to y1."""

    shape = cq.Workplane("XZ").polyline(points).close().extrude(y1 - y0)
    bb = shape.val().BoundingBox()
    return shape.translate((0, y0 - bb.ymin, 0))


def prism_yz(points, x0, x1):
    """A closed (y, z) outline, extruded along X from x0 to x1."""

    return (cq.Workplane("YZ").polyline(points).close().extrude(x1 - x0)
            .translate((x0, 0, 0)))


def hex_prism(across_flats, z0, z1, x=0.0, y=0.0):
    return (cq.Workplane("XY").polygon(6, 2.0 * across_flats / math.sqrt(3.0))
            .extrude(z1 - z0).translate((x, y, z0)))


def cone_z(r0, r1, z0, z1, x=0.0, y=0.0):
    """Cone from radius r0 at z0 to r1 at z1."""

    return cq.Workplane("XY").add(cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(x, y, z0),
                                                    cq.Vector(0, 0, 1)))


def revolve(points):
    """Solid from a closed (r, z) half section turned round the Z axis."""

    wp = cq.Workplane("XZ").moveTo(*points[0])
    for point in points[1:]:
        if point[0] == "arc":
            wp = wp.threePointArc(point[1], point[2])
        else:
            wp = wp.lineTo(*point)
    return wp.close().revolve(360.0, (0, 0, 0), (0, 1, 0))


def arc_middle(centre, radius, angle0, angle1):
    angle = math.radians((angle0 + angle1) / 2.0)
    return (centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle))


def rounded(shape, selector, radius, what):
    """Fillet the selected edges, or leave them sharp if OCC refuses."""

    try:
        return shape.edges(selector).fillet(radius)
    except Exception as exc:
        print(f"WARNING: {what} fillet skipped: {exc}")
        return shape


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


def bottle_shape(height, squeeze=0.0, z0=None):
    """The bottle's lower part standing on the floor, squeeze smaller on the radius."""

    z0 = floor_top if z0 is None else z0
    r = CORNER_RADIUS
    centre = (bottle_flat - squeeze, z0 + r)
    return revolve([
        (0.0, z0),
        (centre[0], z0),
        ("arc", arc_middle(centre, r, -90.0, 0.0), (centre[0] + r, centre[1])),
        (bottle_radius(height) - squeeze, z0 + height),
        (0.0, z0 + height),
    ])


# ============================================================
# PARTS (for the fit check and the preview)
# ============================================================

def usb_receptacle_x(x_face, width, height, y_mid, z_mid, length=7.35):
    """Receptacle pointing +X, its face at x_face."""

    return (box(x_face - length, x_face, y_mid - width / 2.0, y_mid + width / 2.0,
                z_mid - height / 2.0, z_mid + height / 2.0)
            .edges("|X").fillet(height / 2.0 - 0.05))


def usb_receptacle_z(z_face, width, height, x_mid, length=7.35):
    """Receptacle pointing +Z (up), its face at z_face, across Y."""

    return (box(x_mid - height / 2.0, x_mid + height / 2.0, -width / 2.0, width / 2.0,
                z_face - length, z_face)
            .edges("|Z").fillet(height / 2.0 - 0.05))


battery = box(batt_x0, batt_x1, -BATT_LENGTH / 2.0, BATT_LENGTH / 2.0, batt_z0, batt_z1)

tp_pcb = box(tp_x0, tp_x1, tp_y - TP_WIDTH / 2.0, tp_y + TP_WIDTH / 2.0, tp_z0, tp_top)
tp_usb = usb_receptacle_x(tp_face_x, TP_USB_WIDTH, TP_USB_HEIGHT, pwr_y, tp_usb_z)
tp_parts = box(tp_x0 + 1.0, tp_x1 - 8.0, tp_y - TP_WIDTH / 2.0 + 1.0, tp_y + TP_WIDTH / 2.0 - 1.0,
               tp_top, tp_top + TP_PARTS)
charger = union_all([tp_pcb, tp_usb, tp_parts])

c3_pcb = (box(c3_back, c3_face, -C3_WIDTH / 2.0, C3_WIDTH / 2.0, c3_z0, c3_z1)
          .edges("|X").fillet(1.0))
c3_under = box(c3_back - C3_UNDER, c3_back, -C3_WIDTH / 2.0 + 3.0, C3_WIDTH / 2.0 - 3.0,
               c3_z0 + 2.0, c3_z1 - 2.0)
c3_usb = usb_receptacle_z(c3_usb_top, C3_USB_WIDTH, C3_USB_HEIGHT, c3_usb_x)
c3_glass = box(c3_face, glass_front, -C3_GLASS_WIDTH / 2.0, C3_GLASS_WIDTH / 2.0, glass_z0, glass_z1)
c3_lit = box(glass_front, glass_front + 0.02,
             screen_y - C3_SCREEN_WIDTH / 2.0, screen_y + C3_SCREEN_WIDTH / 2.0,
             screen_z - C3_SCREEN_HEIGHT / 2.0, screen_z + C3_SCREEN_HEIGHT / 2.0)
buttons = union_all([box(c3_face, button_front, y - 2.2, y + 2.2, button_z - 1.7, button_z + 1.7)
                     for y in (boot_y, rst_y)])
c3_board = union_all([c3_pcb, c3_under, c3_usb, c3_glass, buttons])

airtag = rounded(rounded(cylinder_z(AIRTAG_DIAMETER / 2.0, pocket_floor,
                                    pocket_floor + AIRTAG_THICKNESS, airtag_x),
                         "<Z", 3.0, "AirTag dome"), ">Z", 1.0, "AirTag top")

# Cable plugs, pushed fully home.
prg_plug = box(c3_usb_x - PLUG_THICKNESS / 2.0, c3_usb_x + PLUG_THICKNESS / 2.0,
               -PLUG_WIDTH / 2.0, PLUG_WIDTH / 2.0, tower_top + 0.3, tower_top + 0.3 + PLUG_LENGTH)
pwr_plug = box(face_x + 0.3, face_x + 0.3 + PLUG_LENGTH,
               pwr_y - PLUG_WIDTH / 2.0, pwr_y + PLUG_WIDTH / 2.0,
               tp_usb_z - PLUG_THICKNESS / 2.0, tp_usb_z + PLUG_THICKNESS / 2.0)
if tp_usb_z - PLUG_THICKNESS / 2.0 < 0.3:
    error("a PWR plug would touch the table; raise the TP4056")

# Screws and nuts, done up.
shank_r = SCREW_HOLE / 2.0 - 0.2
screws = union_all([cylinder_z(HEAD_DIAMETER / 2.0, head_z0, head_top, x, y)
                    .union(cylinder_z(shank_r, head_top - 0.5, screw_tip, x, y))
                    for x, y in screw_spots])
nuts = union_all([hex_prism(NUT_WIDTH, nut_z0, nut_top, x, y)
                  .cut(cylinder_z(shank_r, 0.0, 40.0, x, y))
                  for x, y in screw_spots])


# ============================================================
# POD (PETG)
# ============================================================

label_spots = {}


def pod_outline(z0, z1, grow=0.0, tower=True):
    """The pod's outside (tray and tower), grow bigger on every side."""

    g = grow
    shapes = [
        rounded(box(tray_x0 - g, batt_zone_x1 + g, -batt_half - g, batt_half + g, z0, z1),
                "|Z", 2.0, "tray corner"),
        box(batt_x1, face_x + g, -tower_half - g, tower_half + g, z0, z1),
    ]
    if tower:
        shapes.append(box(tower_x0 - g, face_x + g, -tower_half - g, tower_half + g, z0, tower_top + g))
    return union_all(shapes)


def fastener_outline(z0, z1, grow=0.0, clips=True):
    """The screw columns (joined to the tray's sides) and the clips' arms."""

    g = grow
    shapes = []
    for x, y in screw_spots:
        y0, y1 = sorted((math.copysign(batt_half - 0.5, y), y))
        shapes.append(cylinder_z(boss_r + g, z0, z1, x, y))
        shapes.append(box(x - boss_r - g, x + boss_r + g, y0, y1, z0, z1))
    if clips:
        for sign in (1.0, -1.0):
            y0, y1 = sorted((sign * (batt_half - 0.5), sign * (clip_y1 + g)))
            shapes.append(box(step_x0 - g, step_x1 + g, y0, y1, z0, z1))   # the lid's step too
    return union_all(shapes)


def make_pod():

    pod = pod_outline(pod_z0, lid_z0)
    pod = rounded(pod, "|Z and >X", 1.2, "face corners")

    # Inside: tray, and the tower open on the bottle side.
    pod = pod.cut(box(tray_in_x0, batt_x1 + CLEARANCE, -batt_in_half, batt_in_half, pod_in, lid_z0 + 1.0))
    pod = pod.cut(box(batt_x1, face_in, -tower_in_half, tower_in_half, pod_in, lid_z0 + 1.0))
    pod = pod.cut(box(tower_x0 - 1.0, face_in, -tower_in_half, tower_in_half, pod_in, tower_in))
    # Behind the lid's wall only the side walls (the bottle is there).
    pod = pod.cut(box(tower_x0 - 1.0, groove_x0 + 0.01, -tower_in_half, tower_in_half, pod_in, big))
    # Grooves for the lid's wall, open at the top: the wall drops in and
    # closes the tower's top there.
    pod = pod.cut(box(groove_x0, groove_x1, -groove_half, groove_half, lid_z0, big))
    # The top open on to the C3's back, so the lid's pegs go down past
    # it; the lid's cap fills it.
    pod = pod.cut(box(groove_x1 - 0.01, c3_back + 0.15, -tower_in_half, tower_in_half, tower_in - 0.01, big))

    # Ribs on the face's inside along the C3's edges (its screen side
    # stands on them), and posts under its bottom edge.
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * rib_in, sign * (tower_in_half + 0.1)))
        pod = pod.union(box(c3_face, face_in + 0.1, y0, y1, pod_in - 0.1, c3_z1))
        pod = pod.union(box(c3_back, c3_face + 0.01, y0, y1, pod_in - 0.1, c3_z0))

    # Board lips: the side walls in front of the grooves are tongues,
    # hinged at the bottom (slots at the back, the front and the top),
    # with two lips over the C3's back edges: flat on the board side,
    # 45 degrees on the lead-in and underneath (prints without support).
    # The C3 pushed in spreads the tongues and snaps past the lips.
    tongue_x0 = groove_x1 - LIP_SLOT
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * (tower_in_half - 0.01), sign * (tower_half + 1.0)))
        for x0, x1 in ((tongue_x0, groove_x1), (tongue_x1, tongue_x1 + LIP_SLOT)):
            pod = pod.cut(box(x0, x1, y0, y1, tongue_z0, tongue_z1 + LIP_SLOT))
        pod = pod.cut(box(tongue_x0, tongue_x1 + LIP_SLOT, y0, y1, tongue_z1, tongue_z1 + LIP_SLOT))
        wall_y = sign * (tower_in_half + 0.01)
        for lz in lip_zs:
            plan = (cq.Workplane("XY")
                    .polyline([(lip_x0, wall_y), (lip_x1, sign * lip_tip), (lip_x1, wall_y)]).close()
                    .extrude(BOARD_LIP_HEIGHT).translate((0, 0, lz)))
            side = prism_yz([(wall_y, lz), (sign * lip_tip, lz + lip_depth),
                             (sign * lip_tip, lz + BOARD_LIP_HEIGHT), (wall_y, lz + BOARD_LIP_HEIGHT)],
                            lip_x0 - 0.1, lip_x1 + 0.1)
            pod = pod.union(plan.intersect(side))

    # Screw columns beside the battery: screw hole, hex nut pocket open
    # underneath (the nut goes in from below; the screw pulls it up).
    pod = pod.union(fastener_outline(pod_z0, lid_z0, clips=False))
    for x, y in screw_spots:
        pod = pod.cut(cylinder_z(SCREW_HOLE / 2.0, -1.0, lid_z0 + 1.0, x, y))
        pod = pod.cut(cylinder_z(bore_r, -1.0, head_top, x, y))

    # Clips: an arm outside each side of the tray, joined to it at the
    # bottom only, up to the lid's top, with a hook over the lid's step
    # (flat underneath, ramped on top so the lid pushes it out going down).
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * clip_y0, sign * clip_y1))
        pod = pod.union(box(clip_x0, clip_x1, y0, y1, pod_z0, lid_z1))
        y0, y1 = sorted((sign * (batt_half - 0.1), sign * (clip_y0 + 0.1)))
        pod = pod.union(box(clip_x0, clip_x1, y0, y1, pod_z0, pod_z0 + CLIP_ROOT))
        pod = pod.union(prism_yz([(sign * (clip_y0 + 0.01), hook_z),
                                  (sign * (clip_y0 - CLIP_HOOK), hook_z),
                                  (sign * (clip_y0 + 0.01), lid_z1)], clip_x0, clip_x1))

    # Bezel round the window, up to just short of the glass.
    if bezel_x0 < face_in:
        pod = pod.union(box(bezel_x0, face_in + 0.1, screen_y - bezel_hy, screen_y + bezel_hy,
                            screen_z - bezel_hz, screen_z + bezel_hz))

    # Window, bevelled on the outside.
    pod = pod.cut(box(bezel_x0 - 0.1, face_x + 0.1, screen_y - window_hy, screen_y + window_hy,
                      screen_z - window_hz, screen_z + window_hz))
    ch = WINDOW_CHAMFER
    plane = cq.Plane(origin=(face_x + 0.2, screen_y, screen_z), xDir=(0, 1, 0), normal=(-1, 0, 0))
    pod = pod.cut(cq.Workplane(plane)
                  .rect(2 * (window_hy + ch + 0.2), 2 * (window_hz + ch + 0.2))
                  .workplane(offset=ch + 0.2)
                  .rect(2 * window_hy, 2 * window_hz)
                  .loft())

    # BOOT flexure: U-shaped slot, tab thinned from inside, nub behind it.
    pod = pod.cut(box(face_in - 1.0, face_x + 0.1, boot_y - flex_hy - s, boot_y + flex_hy + s,
                      flex_z0, flex_z1 + s))
    pod = pod.union(box(face_x - FLEX_THICKNESS, face_x, boot_y - flex_hy, boot_y + flex_hy,
                        flex_z0 - 0.01, flex_z1))
    pod = pod.union(cylinder_x(NUB_DIAMETER / 2.0, button_front + NUB_GAP,
                               face_x - FLEX_THICKNESS + 0.01, boot_y, button_z))

    # RST pin hole.
    pod = pod.cut(cylinder_x(RST_HOLE / 2.0, face_in - 1.0, face_x + 0.1, rst_y, button_z))

    # PWR: TP4056 USB-C through the bottom of the face.
    pod = pod.cut(box(face_in - 1.0, face_x + 1.0, pwr_y - pwr_w / 2.0, pwr_y + pwr_w / 2.0,
                      tp_usb_z - pwr_h / 2.0, tp_usb_z + pwr_h / 2.0)
                  .edges("|X").fillet(min(1.2, pwr_h / 2.0 - 0.05)))

    # PRG: C3 USB-C up through the top, as a slot open on the bottle
    # side so the board goes in sideways; the lid's tab fills the rest.
    prg_x1 = c3_face + C3_USB_HEIGHT + PORT_CLEARANCE / 2.0
    pod = pod.cut(box(tower_x0 - 1.0, prg_x1, -prg_w / 2.0, prg_w / 2.0, tower_in - 1.0, tower_top + 1.0))

    # Labels engraved in the face, upright.
    label_spots["PRG"] = (0.0, (glass_z1 + tower_top) / 2.0)
    label_spots["PWR"] = ((boot_y + flex_hy + s + rst_y - RST_HOLE / 2.0) / 2.0,
                          (tp_usb_z + pwr_h / 2.0 + screen_z - window_hz - ch) / 2.0)
    for name, (y, z) in label_spots.items():
        plane = cq.Plane(origin=(face_x + 0.2, y, z), xDir=(0, 1, 0), normal=(1, 0, 0))
        text = cq.Workplane(plane).text(name, LABEL_SIZE, -(LABEL_DEPTH + 0.2),
                                        font=LABEL_FONT, kind="bold",
                                        halign="center", valign="center")
        bb = text.val().BoundingBox()
        if bb.ymin < -opening_half + 0.5 or bb.ymax > opening_half - 0.5:
            error(f"label {name} runs under the frame's lips; make LABEL_SIZE smaller")
        if name == "PWR" and (bb.zmin < tp_usb_z + pwr_h / 2.0 + 0.4
                              or bb.zmax > screen_z - window_hz - ch - 0.4
                              or bb.ymin < boot_y + flex_hy + s + 0.4
                              or bb.ymax > rst_y - RST_HOLE / 2.0 - 0.4):
            error("label PWR does not fit between the port, the window, the BOOT tab and RST")
        pod = pod.cut(text)

    return pod


# ============================================================
# LID (PETG)
# ============================================================

def make_lid():

    # Plate over the tray, stopping 0.15 short of the tower's side walls.
    plate = union_all([
        rounded(box(tray_x0, batt_zone_x1, -batt_half, batt_half, lid_z0, lid_z1), "|Z", 2.0, "plate corner"),
        box(batt_x1, tower_x0 - 0.15, -tower_half, tower_half, lid_z0, lid_z1),
        box(tower_x0 - 0.2, wall_x0 + 0.01, -tower_in_half + 0.15, tower_in_half - 0.15, lid_z0, lid_z1),
    ])

    # Over the screw columns, and out to the clips' arms.
    plate = plate.union(fastener_outline(lid_z0, lid_z1, clips=False))
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * (batt_half - 1.0), sign * (clip_y0 - 0.15)))
        plate = plate.union(box(step_x0, step_x1, y0, y1, lid_z0, lid_z1))

    # Wall closing the tower on the bottle side, its edges in the grooves
    # in the tower's side walls, up to the tower's top.
    lid = plate.union(box(wall_x0, wall_x1, -lid_wall_half, lid_wall_half, lid_z0, tower_top))

    # Cap filling the tower's top over the C3's back, on a 45 degree
    # gusset so it prints.
    cap_half = tower_in_half - 0.15
    lid = lid.union(box(wall_x0, c3_back, -cap_half, cap_half, tower_in, tower_top))
    g = c3_back - wall_x1
    lid = lid.union(prism_xz([(wall_x1 - 0.01, tower_in - g), (wall_x1 + g, tower_in + 0.01),
                              (wall_x1 - 0.01, tower_in + 0.01)], -cap_half, cap_half))

    # Screw holes, and the nut pockets open at the top.
    for x, y in screw_spots:
        lid = lid.cut(cylinder_z(SCREW_HOLE / 2.0, lid_z0 - 1.0, lid_z1 + 1.0, x, y))
        lid = lid.cut(hex_prism(nut_hole_af, nut_z0, lid_z1 + 1.0, x, y))

    # Step in the plate's edge under each clip's hook.
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * (clip_y0 - CLIP_HOOK - 0.3), sign * (clip_y0 + 1.0)))
        lid = lid.cut(box(step_x0, step_x1, y0, y1, hook_z, lid_z1 + 1.0))

    # Tab filling the PRG slot behind the receptacle, on a 45 degree
    # gusset so it prints.
    tab_x1 = c3_face - PORT_CLEARANCE / 2.0
    tab_half = prg_w / 2.0 - 0.15
    lid = lid.union(box(wall_x0, tab_x1, -tab_half, tab_half, tower_in - 0.2, tower_top))
    g = tab_x1 - wall_x1                    # clears the C3 top edge (fit check)
    lid = lid.union(prism_xz([(wall_x1 - 0.01, tower_in - 0.2 - g), (wall_x1 + g, tower_in - 0.19),
                              (wall_x1 - 0.01, tower_in - 0.19)], -tab_half, tab_half))

    # Pegs pressing the C3 onto its ribs, clear of the wire pads at its
    # USB end, with 45 degree undersides; inside the board lips, so they
    # pass them as the lid goes down.
    d = c3_back - wall_x1
    for z in peg_zs:
        for sign in (1.0, -1.0):
            y = sign * (lip_tip - 0.2 - PEG / 2.0)
            if z - d >= lid_z0:
                outline = [(wall_x1 - 0.01, z - d), (c3_back, z)]
            else:
                # Low peg: stands on the plate's underside level (the bed)
                # instead of hanging below it.
                outline = [(wall_x1 - 0.01, lid_z0), (c3_back, lid_z0)]
            outline += [(c3_back, z + PEG), (wall_x1 - 0.01, z + PEG)]
            lid = lid.union(prism_xz(outline, y - PEG / 2.0, y + PEG / 2.0))

    return lid


# ============================================================
# BOOT (TPU)
# ============================================================

def drain_spots():
    """Drain holes round the floor, leaving out the ones that hit a pocket."""

    r = DRAIN_DIAMETER / 2.0
    ring = inner_flat - r - 0.5
    spots = []
    for i in range(DRAIN_HOLES):
        a = 2.0 * math.pi * (i + 0.5) / DRAIN_HOLES
        x, y = ring * math.cos(a), ring * math.sin(a)
        if math.hypot(x - airtag_x, y) < pocket_radius + r + 1.0:
            continue
        if x > tray_x0 - r - 1.0 and abs(y) < batt_half + r + 1.0:
            continue
        if any(math.hypot(x - sx, y - sy) < boss_r + r + 1.5 for sx, sy in screw_spots):
            continue
        if clip_x0 - r - 1.5 < x < clip_x1 + r + 1.5 and abs(y) < clip_y1 + r + 1.5:
            continue
        spots.append((x, y))
    return spots


def make_boot(pod_fit):

    bottom_centre = (outer_bottom - BOTTOM_ROUND, BOTTOM_ROUND)
    boot = revolve([
        (0.0, 0.0),
        (bottom_centre[0], 0.0),
        ("arc", arc_middle(bottom_centre, BOTTOM_ROUND, -90.0, 0.0), (outer_bottom, BOTTOM_ROUND)),
        (outer_radius(top_z), top_z),
        (0.0, top_z),
    ])

    # Frame round the tower.
    frame = box(inner_flat - 5.0, face_x + FRAME_FRONT, -frame_half, frame_half, 0.0, tower_top)
    frame = rounded(frame, "|Z and >X", 2.0, "frame corners")
    frame = rounded(frame, "<Z and >X", 1.0, "frame bottom edge")
    boot = boot.union(frame)

    # The bottle's place, a little small so the TPU grips.
    boot = boot.cut(bottle_shape(top_z - floor_top + 5.0, squeeze=c))
    boot = rounded(boot, ">Z", TOP_ROUND, "top edge")

    # Pod pocket, open at the top for the tray and on the bottle side for
    # the tower; the frame's opening leaves lips over the face's edges.
    boot = boot.cut(pod_outline(pod_z0, floor_top + 0.01, grow=pod_fit / 2.0, tower=False))
    boot = boot.cut(fastener_outline(pod_z0, floor_top + 0.01, grow=pod_fit / 2.0))
    # The tower's place: only its own outline (TPU behind it, round the
    # bottle), under the back strap; the tower goes in from underneath,
    # stretching the TPU.
    h = tower_half + pod_fit / 2.0
    boot = boot.cut(box(tower_x0 - pod_fit / 2.0, face_x + pod_fit / 2.0, -h, h, pod_z0, back_z0))
    boot = boot.cut(box(back_x1, face_x + pod_fit / 2.0, -h, h, pod_z0, big))
    boot = boot.cut(box(face_x - 1.0, big, -opening_half, opening_half, pod_z0, big))
    # Strap across the face above the window, closing the boot's ring.
    boot = boot.union(prism_yz([(-strap_half, tower_top), (strap_half, tower_top),
                                (strap_half, strap_underside(strap_half)), (0.0, strap_apex),
                                (-strap_half, strap_underside(strap_half))],
                               face_x + pod_fit / 2.0, face_x + STRAP))

    # AirTag pocket: lead-in chamfer down to the lip, then the pocket.
    pocket = revolve([
        (0.0, pocket_floor), (pocket_radius, pocket_floor), (pocket_radius, pocket_top),
        (lip_radius, pocket_top), (pocket_radius, floor_top + 0.01),
        (pocket_radius, floor_top + 1.0), (0.0, floor_top + 1.0),
    ]).translate((airtag_x, 0, 0))
    boot = boot.cut(pocket)
    boot = boot.cut(cylinder_z(push_radius, -1.0, pocket_floor + 0.1, airtag_x))
    if SOUND_HOLES:
        holes = (cq.Workplane("XY").polarArray(sound_ring, 0.0, 360.0, SOUND_HOLES)
                 .circle(sound_radius).extrude(pocket_floor + 2.0)
                 .translate((airtag_x, 0, -1.0)))
        boot = boot.cut(holes)
    if SPRING_BUMPS:
        bumps = (cq.Workplane("XY").polarArray(spring_ring, 45.0, 360.0, SPRING_BUMPS)
                 .circle(spring_radius).extrude(SPRING_HEIGHT + 0.1)
                 .translate((airtag_x, 0, pocket_floor - 0.1)))
        bumps = rounded(bumps, ">Z", min(0.3, SPRING_HEIGHT * 0.75), "spring bump tops")
        boot = boot.union(bumps)

    for x, y in drain_spots():
        boot = boot.cut(cylinder_z(DRAIN_DIAMETER / 2.0, -1.0, floor_top + 1.0, x, y))

    return boot


stage("Building pod")
pod = make_pod()
stage("Building lid")
lid = make_lid()
stage("Building boot")
boot = make_boot(POD_FIT)


# ============================================================
# FIT CHECK
# ============================================================

if CHECK_FIT:
    stage("Checking fit")
    boot_loose = make_boot(0.0) if POD_FIT < 0.0 else boot   # the press fit overlaps on purpose
    bottle = bottle_shape(60.0)
    parts = {"battery": battery, "charger": charger, "C3 board": c3_board,
             "screws": screws, "nuts": nuts}
    tests = []
    for name, shape in parts.items():
        tests.append((f"{name} hits the pod", shape, pod))
        tests.append((f"{name} hits the lid", shape, lid))
    tests += [
        ("battery hits the charger", battery, charger),
        ("battery hits the screws", battery, screws.union(nuts)),
        ("AirTag hits the lid", airtag, lid),
        ("charger hits the C3 board", charger, c3_board),
        ("pod hits the lid", pod, lid),
        ("pod hits the boot", pod, boot_loose),
        ("lid hits the boot", lid, boot_loose),
        ("AirTag hits the pod", airtag, pod),
        ("bottle hits the pod", bottle, pod),
        ("bottle hits the lid", bottle, lid),
        ("bottle hits the AirTag", bottle, airtag),
        ("PRG plug hits the boot", prg_plug, boot),
        ("PRG plug hits the bottle", prg_plug, bottle_shape(80.0)),
        ("PRG plug hits the pod", prg_plug, pod),
        ("PWR plug hits the boot", pwr_plug, boot),
        ("PWR plug hits the pod", pwr_plug, pod),
    ]
    if AIRTAG_CLEARANCE >= 0.0:
        tests.append(("AirTag hits the boot", airtag, boot))
    # The lid goes straight down: on the way, only the clips (which
    # spring out) may touch it.
    pod_rigid = pod.cut(fastener_outline(-1.0, big, clips=True).cut(
        fastener_outline(-2.0, big + 1.0, clips=False)))
    for dz in (1.0, 4.0, 9.0, 16.0, 24.0):
        raised = lid.translate((0, 0, dz))
        tests.append((f"lid, {dz:g} up on its way down, hits the pod", raised, pod_rigid))
        tests.append((f"lid, {dz:g} up on its way down, hits the C3 board", raised, c3_board))
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
# PREVIEW IMAGE
# ============================================================

COLORS = {
    "boot": (0.25, 0.55, 0.85),
    "pod": (0.55, 0.56, 0.58),
    "lid": (0.70, 0.71, 0.73),
    "battery": (0.85, 0.80, 0.45),
    "charger": (0.15, 0.18, 0.22),
    "c3": (0.45, 0.25, 0.60),
    "usb": (0.85, 0.85, 0.88),
    "glass": (0.08, 0.08, 0.10),
    "lit": (0.95, 0.95, 0.95),
    "airtag": (0.96, 0.96, 0.96),
    "bottle": (0.93, 0.55, 0.45),
}


def mesh(shape, color):

    import numpy as np

    vertices, triangles = cq.Compound.makeCompound(shape.vals()).tessellate(0.2, 0.5)
    if not triangles:
        return np.zeros((0, 3, 3)), np.zeros((0, 3))
    xyz = np.array([(v.x, v.y, v.z) for v in vertices])
    tris = xyz[np.array(triangles, dtype=int)]

    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    normals = normals / np.where(lengths == 0.0, 1.0, lengths)[:, None]

    light = np.array([0.5, -0.6, 0.65])
    light = light / np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.abs(normals @ light)
    return tris, shade[:, None] * np.array(color)


def face_drawing(ax, title):
    """The tower's face, drawn flat from the model's numbers."""

    import matplotlib.patches as patches

    def rect(y0, y1, z0, z1, color, z, label=None, round_=0.0):
        ax.add_patch(patches.FancyBboxPatch(
            (y0, z0), y1 - y0, z1 - z0, boxstyle=f"round,pad=0,rounding_size={round_}",
            facecolor=color, edgecolor="0.2", linewidth=0.6, zorder=z, label=label))

    rect(-frame_half, frame_half, 0.0, tower_top, COLORS["boot"], 1, "TPU frame", 1.5)
    rect(-opening_half, opening_half, pod_z0, tower_top + 0.01, COLORS["pod"], 2, "pod face")
    ax.add_patch(patches.Polygon(
        [(-strap_half, tower_top), (strap_half, tower_top), (strap_half, strap_underside(strap_half)),
         (0.0, strap_apex), (-strap_half, strap_underside(strap_half))],
        facecolor=COLORS["boot"], edgecolor="0.2", linewidth=0.6, zorder=7, alpha=0.85,
        label="TPU strap"))
    rect(screen_y - window_hy, screen_y + window_hy, screen_z - window_hz, screen_z + window_hz,
         "0.05", 4, "window")
    ax.add_patch(patches.Rectangle((screen_y - C3_SCREEN_WIDTH / 2.0, screen_z - C3_SCREEN_HEIGHT / 2.0),
                                   C3_SCREEN_WIDTH, C3_SCREEN_HEIGHT, facecolor="0.85", zorder=5))
    rect(boot_y - flex_hy - s, boot_y + flex_hy + s, flex_z0, flex_z1 + s, "white", 4)
    rect(boot_y - flex_hy, boot_y + flex_hy, flex_z0, flex_z1, COLORS["lid"], 5, "BOOT tab")
    ax.add_patch(patches.Circle((rst_y, button_z), RST_HOLE / 2.0, color="0.05", zorder=5))
    rect(pwr_y - pwr_w / 2.0, pwr_y + pwr_w / 2.0, tp_usb_z - pwr_h / 2.0, tp_usb_z + pwr_h / 2.0,
         "0.05", 4, "PWR port", 1.2)
    rect(-prg_w / 2.0, prg_w / 2.0, tower_top, tower_top + 1.5, "0.05", 4, "PRG port (on top)", 0.5)
    for name, (y, z) in label_spots.items():
        ax.text(y, z, name, ha="center", va="center", fontsize=8, fontweight="bold",
                color="0.15", zorder=6)
    ax.text(rst_y, button_z + 1.2, "RST", ha="center", va="bottom", fontsize=6, zorder=6)
    ax.set_xlim(-frame_half - 3.0, frame_half + 3.0)
    ax.set_ylim(-2.0, tower_top + 4.0)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.3)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title(title, fontsize=10)


def floor_drawing(ax, title):
    """The floor seen from above: what lies where."""

    import matplotlib.patches as patches

    def rect(x0, x1, y0, y1, color, z, label=None, edge="0.2"):
        ax.add_patch(patches.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color,
                                       edgecolor=edge, linewidth=0.6, zorder=z, label=label))

    ax.add_patch(patches.Circle((0, 0), outer_radius(floor_top), facecolor=COLORS["boot"],
                                edgecolor="0.2", zorder=1, label="boot (TPU)"))
    rect(inner_flat - 5.0, face_x + FRAME_FRONT, -frame_half, frame_half, COLORS["boot"], 1)
    ax.add_patch(patches.Circle((0, 0), bottle_radius(0.0), fill=False, linestyle="--",
                                edgecolor="0.3", zorder=8, label="bottle"))
    rect(tray_x0, batt_zone_x1, -batt_half, batt_half, COLORS["pod"], 2, "pod (PETG)")
    rect(batt_x1, face_x, -tower_half, tower_half, COLORS["pod"], 2)
    rect(batt_x0, batt_x1, -BATT_LENGTH / 2.0, BATT_LENGTH / 2.0, COLORS["battery"], 3, "battery")
    rect(tp_x0, tp_x1, tp_y - TP_WIDTH / 2.0, tp_y + TP_WIDTH / 2.0, COLORS["charger"], 3, "TP4056")
    rect(c3_back, c3_face, -C3_WIDTH / 2.0, C3_WIDTH / 2.0, COLORS["c3"], 4, "C3 (upright)")
    rect(wall_x0, wall_x1, -lid_wall_half, lid_wall_half, COLORS["lid"], 4, "lid wall")
    for i, (x, y) in enumerate(screw_spots):
        ax.add_patch(patches.Circle((x, y), boss_r, facecolor=COLORS["pod"], edgecolor="0.2", zorder=2))
        ax.add_patch(patches.RegularPolygon((x, y), 6, radius=NUT_WIDTH / math.sqrt(3.0),
                                            orientation=math.pi / 6.0, facecolor=COLORS["usb"],
                                            edgecolor="0.2", zorder=4,
                                            label=None if i else "M3 nuts (screws from under)"))
    for sign in (1.0, -1.0):
        y0, y1 = sorted((sign * clip_y0, sign * clip_y1))
        rect(clip_x0, clip_x1, y0, y1, "0.25", 4, "clips" if sign > 0 else None)
    ax.add_patch(patches.Circle((airtag_x, 0), AIRTAG_DIAMETER / 2.0, facecolor=COLORS["airtag"],
                                edgecolor="0.2", zorder=3, label="AirTag"))
    for x, y in drain_spots():
        ax.add_patch(patches.Circle((x, y), DRAIN_DIAMETER / 2.0, color="white", zorder=5))
    ax.annotate("screen, PWR", (face_x + FRAME_FRONT, 0), (face_x + 6, -frame_half - 8),
                fontsize=7, arrowprops={"arrowstyle": "->"})
    lim = face_x + 8.0
    ax.set_xlim(-lim + 4.0, lim)
    ax.set_ylim(-lim + 4.0, lim - 4.0)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.3)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, loc="upper left")
    ax.set_title(title, fontsize=10)


def render_preview(filename):

    import numpy as np
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    inside = [
        (battery, "battery"), (tp_pcb.union(tp_parts), "charger"), (tp_usb, "usb"),
        (c3_pcb.union(c3_under).union(buttons), "c3"), (c3_usb, "usb"),
        (c3_glass, "glass"), (c3_lit, "lit"), (screws, "usb"), (nuts, "usb"),
    ]

    # Each part is tessellated once and moved as triangles.
    cache = {}

    def tri_mesh(shape, color_name):
        key = id(shape)
        if key not in cache:
            cache[key] = (shape, mesh(shape, COLORS[color_name]))
        return cache[key][1]

    def shifted(items, dz=0.0, dx=0.0):
        return [(shape, color, (dx, 0.0, dz)) for shape, color, *_ in items]

    bottle_stub = bottle_shape(45.0)
    assembled = [(boot, "boot"), (pod, "pod"), (lid, "lid"), (c3_lit, "lit"),
                 (bottle_stub.intersect(box(-big, big, -big, big, top_z - 1.0, big)), "bottle")]
    exploded = ([(boot, "boot"), (airtag, "airtag", (0.0, 0.0, 30.0))]
                + shifted([(pod, "pod")] + inside, dz=45.0, dx=25.0)
                + [(lid, "lid", (10.0, 0.0, 85.0))])

    keep = box(-big, big, 0.0, big, -big, big)
    section = [(shape.intersect(keep), color)
               for shape, color in [(boot, "boot"), (pod, "pod"), (lid, "lid"), (airtag, "airtag"),
                                    (bottle_stub, "bottle")] + inside]
    pod_back = [(pod, "pod"), (lid, "lid", (0.0, 0.0, 16.0))]

    views = [
        ("Tower face (mm)", "face", None, None),
        ("Floor from above (mm)", "floor", None, None),
        ("Assembled, bottle in (cut at the boot's top)", assembled, 25, -30),
        ("Exploded", exploded, 20, -60),
        ("Section through the middle", section, 0, -90),
        ("Pod and lid (lid lifted), bottle side", pod_back, 30, 150),
    ]

    fig = plt.figure(figsize=(15, 10))

    for index, (title, items, elevation, azimuth) in enumerate(views):
        if items == "face":
            face_drawing(fig.add_subplot(2, 3, index + 1), title)
            continue
        if items == "floor":
            floor_drawing(fig.add_subplot(2, 3, index + 1), title)
            continue
        stage(f"  view: {title}")
        ax = fig.add_subplot(2, 3, index + 1, projection="3d")
        all_tris, all_colors = [], []
        for shape, color_name, *offset in items:
            if not shape.vals():
                continue
            tris, colors = tri_mesh(shape, color_name)
            if offset:
                tris = tris + np.array(offset[0])
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
        f"c3-pal boot for the Owala FreeSip Sway - {2 * outer_radius(0):.1f} across, "
        f"{face_x + FRAME_FRONT + outer_radius(0):.1f} with the tower, {top_z:.1f} tall; "
        f"bottle raised {floor_top:.1f}",
        fontsize=12)
    fig.tight_layout()
    fig.savefig(HERE / filename, dpi=130)


written = []

if __name__ == "__main__" and PREVIEW:
    stage("Rendering preview")
    try:
        render_preview(PREVIEW_FILE)
        written.append(PREVIEW_FILE)
    except ImportError:
        print("Preview skipped (python -m pip install matplotlib)")
    except Exception as exc:
        print(f"WARNING: Preview failed: {exc}")


# ============================================================
# EXPORT (print orientation)
# ============================================================

# After the preview: the fine STL meshing stays on the shapes, and the
# preview would then draw millions of triangles.

if __name__ == "__main__":

    stage("Writing STLs")
    print_parts = {
        "boot": (boot, BOOT_TOLERANCE, BOOT_ANGULAR_TOLERANCE),
        "pod": (to_bed(pod), STL_TOLERANCE, STL_ANGULAR_TOLERANCE),
        "pod_lid": (to_bed(lid), STL_TOLERANCE, STL_ANGULAR_TOLERANCE),
    }
    for name, (shape, tolerance, angular) in print_parts.items():
        filename = HERE / f"{OUTPUT_PREFIX}_{name}.stl"
        cq.exporters.export(shape, str(filename), tolerance=tolerance, angularTolerance=angular)
        written.append(filename.name)


# ============================================================
# FINAL REPORT
# ============================================================

if __name__ == "__main__":

    tpu_g = volume(boot) / 1000.0 * TPU_DENSITY
    petg_g = (volume(pod) + volume(lid)) / 1000.0 * PETG_DENSITY

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
    print(f"  Boot:      {2 * outer_radius(0):.1f} across, {top_z:.1f} tall, "
          f"tower frame out to x = {face_x + FRAME_FRONT:.1f} "
          f"({face_x + FRAME_FRONT - outer_radius(0):.1f} past the wall)")
    print(f"  Floor:     bottle raised {floor_top:.1f}; AirTag at x = {airtag_x:.1f}, "
          f"{pocket_floor:.1f} of TPU under it")
    print(f"  Up:        pod {pod_z0:.1f}, battery {batt_z0:.1f}-{batt_z1:.1f}, "
          f"lid {lid_z0:.1f}-{lid_z1:.1f}, C3 {c3_z0:.1f}-{c3_z1:.1f}, tower top {tower_top:.1f}")
    print(f"  Out:       AirTag {airtag_x - pocket_radius:.1f}..{airtag_x + pocket_radius:.1f}, "
          f"tray from {tray_x0:.1f}, battery {batt_x0:.1f}-{batt_x1:.1f}, "
          f"TP4056 {tp_x0:.1f}-{tp_x1:.1f}, lid wall {wall_x0:.1f}, C3 PCB {c3_back:.1f}-{c3_face:.1f}, "
          f"face {face_in:.1f}-{face_x:.1f}")
    print(f"  Face:      window centre {screen_z:.1f} up, BOOT {button_z:.1f} up at y = {boot_y:.1f}, "
          f"PWR {tp_usb_z:.1f} up at y = {pwr_y:.1f}")
    print(f"  Fixing:    2x M3x{SCREW_LENGTH:g} socket head from under + M3 nuts in the lid at x = {screw_x:.1f}, "
          f"y = +-{screw_y:.1f}; clips at x = {clip_x0:.1f}-{clip_x1:.1f}; "
          f"lid wall in grooves {GROOVE:g} deep, {KEEPER:g} of wall behind")
    print(f"  Strap:     across the face, z = {strap_apex:.1f}-{tower_top:.1f} in the middle "
          f"(from {strap_underside(strap_half):.1f} at the sides), {STRAP:g} thick; "
          f"back strap: wall whole over the tower, {back_z0:.1f}-{top_z:.1f}")
    print(f"  Weight:    boot {tpu_g:.0f} g TPU, pod + lid {petg_g:.0f} g PETG (solid)")
    print()
    print("Print: boot (TPU 90A) floor down; pod floor down; lid plate down. No supports.")
    print("Firmware: the screen is upside down compared with the bar (build env 'boot').")
    print("=============================================================")
    if errors:
        sys.exit(1)
