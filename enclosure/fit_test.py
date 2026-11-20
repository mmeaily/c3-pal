"""
Fit test pieces for the c3-pal bottle bar
=========================================

Three quick prints cut from the real parts, to check the measured board
sizes before printing the whole case:

    fit_test/fit_prg_end.stl    the bottom end of the front: does the C3's
                                USB-C line up with the PRG opening when
                                the board lies face down on its ribs, can
                                a cable plug in fully?
    fit_test/fit_screen.stl     the front round the window: lay the C3 in
                                face down - does the window frame the lit
                                area, does the tab press BOOT, does a
                                paperclip reach RST?
    fit_test/fit_pwr_end.stl    the top end of the front: does the
                                TP4056's USB-C line up with the PWR
                                opening?

Run:
    python fit_test.py

Imports generate.py (which builds the parts but skips its own export
and preview when imported).
"""

from pathlib import Path

import cadquery as cq

import generate as g

OUT = Path(__file__).parent / "fit_test"
OUT.mkdir(exist_ok=True)

big = g.big

pieces = {
    "fit_prg_end": g.tub.intersect(g.box(-big, 8.0, -big, big, -big, big)),
    "fit_screen": g.tub.intersect(g.box(g.screen_x - g.bezel_hx - 2.0, g.flex_x1 + 3.0,
                                        -g.outer_half - 0.1, g.outer_half + 0.1, -big, big)),
    "fit_pwr_end": g.tub.intersect(g.box(g.inner_length - 8.0, big, -big, big, -big, big)),
}

for name, shape in pieces.items():
    path = OUT / f"{name}.stl"
    cq.exporters.export(shape, str(path),
                        tolerance=g.STL_TOLERANCE, angularTolerance=g.STL_ANGULAR_TOLERANCE)
    print(f"  {path.relative_to(Path(__file__).parent)}  "
          f"({g.volume(shape) / 1000.0 * g.PLA_DENSITY:.1f} g)")
