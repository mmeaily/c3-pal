"""
Fit test piece for the c3-pal boot
==================================

The boot's grip on the bottle is already proven by the owala boot, so
the test is the new part: the front of the floor with the pod pocket and
the TPU frame round the tower, cut from the real boot.

    fit_test/fit_pod_pocket.stl   (TPU 90A) print it, print the pod (it
                                  is small), and check: does the pod
                                  press into the pocket and stay put
                                  upside down, do the frame's lips hold
                                  the tower's face, can the PWR plug go
                                  in?

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

# The floor's front 2 mm above the pod, plus the frame at full height.
keep = (g.box(g.tray_x0 - 4.0, g.big, -g.big, g.big, -1.0, g.floor_top + 2.0)
        .union(g.box(g.inner_flat - 6.0, g.big, -g.frame_half - 1.0, g.frame_half + 1.0, -1.0, g.big)))
pieces = {
    "fit_pod_pocket": g.boot.intersect(keep),
}

for name, shape in pieces.items():
    path = OUT / f"{name}.stl"
    cq.exporters.export(shape, str(path),
                        tolerance=g.STL_TOLERANCE, angularTolerance=g.STL_ANGULAR_TOLERANCE)
    print(f"  {path.relative_to(Path(__file__).parent)}  "
          f"({g.volume(shape) / 1000.0 * g.TPU_DENSITY:.1f} g)")
