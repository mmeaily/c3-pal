"""
Bambu Studio projects for the c3-pal boot
=========================================

Packs the STLs written by generate.py and fit_test.py into Bambu Studio
project files for the A1, so they open ready to slice:

    c3pal_boot.3mf          the boot, TPU 90A (bambu/tpu90a_boot.json)
    c3pal_pod.3mf           pod and lid side by side, gray PETG
                            (bambu/petg_pod.json)
    fit_test/fit_test.3mf   the TPU fit test piece (if fit_test.py ran)

Settings: bambu/a1_project_settings.config (the A1 project settings,
copied from the owala boots project), then, from the job's settings
file: the system process preset PROCESS_PRESET (if given), filament 1
replaced by the system filament preset FILAMENT_PRESET, the "print" and
"filament" settings on top, and BED_TYPE (if given).  The system presets
are read from the Bambu Studio install (BAMBU_SYSTEM below).

TPU 90A does not go through the AMS lite: feed it from the external
spool and map filament 1 to "Ext" when sending.

Run:
    python make_3mf.py

Check a project slices with the Bambu Studio CLI (sliced output stays
out of the project):
    "C:\Program Files\Bambu Studio\bambu-studio.exe" --slice 0 --outputdir <scratch dir> c3pal_pod.3mf
"""

import json
import os
import sys
import uuid
import zipfile
from pathlib import Path

import numpy as np


HERE = Path(__file__).parent
TEMPLATE = HERE / "bambu" / "a1_project_settings.config"
BAMBU_SYSTEM = Path(os.environ.get("APPDATA", "")) / "BambuStudio" / "system" / "BBL"
APPLICATION = "BambuStudio-02.08.02.61"
BED_CENTRE = (128.0, 128.0)       # A1, 256 x 256
SLOTS = 4                         # filament slots in the template
GAP = 8.0                         # between parts on the plate

PRESET_META = ("name", "inherits", "from", "instantiation", "type", "setting_id",
               "filament_id", "description", "compatible_printers", "compatible_printers_condition",
               "print_settings_id", "version", "is_custom_defined")


# ============================================================
# SETTINGS
# ============================================================

def without_notes(group):

    return {key: value for key, value in group.items() if not key.startswith("_")}


def system_preset(kind, name):
    """A system preset with everything it inherits, as one flat dict."""

    path = BAMBU_SYSTEM / kind / f"{name}.json"
    try:
        with open(path, encoding="utf-8") as file:
            preset = json.load(file)
    except FileNotFoundError:
        sys.exit(f"Bambu Studio preset not found: {path}")

    parent = preset.get("inherits")
    merged = system_preset(kind, parent) if parent else {}
    merged.update(preset)
    return merged


def per_filament(value):

    return value if isinstance(value, list) else [value]


def set_slot(settings, key, values, slot=0):
    """Put one filament's values into slot of a per-filament list."""

    current = settings.get(key)
    if not isinstance(current, list) or len(current) % SLOTS:
        return False
    width = len(current) // SLOTS
    if len(values) != width:
        return False
    settings[key] = current[:slot * width] + values + current[(slot + 1) * width:]
    return True


def set_print(settings, key, value):
    """A process setting, shaped like the template's (list or string)."""

    if key not in settings:
        return False
    if isinstance(settings[key], list) and not isinstance(value, list):
        value = [value]
    settings[key] = value
    return True


def project_settings(overrides_file):

    with open(TEMPLATE, encoding="utf-8") as file:
        settings = json.load(file)
    with open(overrides_file, encoding="utf-8") as file:
        overrides = json.load(file)

    # Process preset (the template's own, 0.20mm Standard, if none given).
    process_name = overrides.get("PROCESS_PRESET", settings.get("print_settings_id", "template"))
    skipped = []
    if "PROCESS_PRESET" in overrides:
        for key, value in system_preset("process", process_name).items():
            if key in PRESET_META:
                continue
            if not set_print(settings, key, value):
                skipped.append(key)
        settings["print_settings_id"] = process_name

    # Filament preset into slot 1.
    filament_name = overrides["FILAMENT_PRESET"]
    preset = system_preset("filament", filament_name)
    for key, value in preset.items():
        if key in PRESET_META:
            continue
        if not set_slot(settings, key, per_filament(value)):
            skipped.append(key)
    set_slot(settings, "filament_settings_id", [filament_name])
    set_slot(settings, "filament_ids", [preset["filament_id"]])

    for key, value in without_notes(overrides["filament"]).items():
        if not set_slot(settings, key, per_filament(value)):
            sys.exit(f"{overrides_file.name}: '{key}' is not a per-filament setting")

    for key, value in without_notes(overrides["print"]).items():
        if not set_print(settings, key, value):
            sys.exit(f"{overrides_file.name}: unknown print setting '{key}'")

    if "BED_TYPE" in overrides:
        settings["curr_bed_type"] = overrides["BED_TYPE"]

    if skipped:
        print(f"  preset keys not in the template, left out: {len(skipped)}")

    return settings, f"{process_name} / {filament_name}"


# ============================================================
# MESH
# ============================================================

def read_stl(path):
    """Binary STL to (vertices, triangles), shared vertices merged."""

    data = path.read_bytes()
    count = int.from_bytes(data[80:84], "little")
    if len(data) != 84 + 50 * count:
        sys.exit(f"{path}: not a binary STL")
    records = np.frombuffer(data, dtype=np.dtype([
        ("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")
    ]), count=count, offset=84)

    corners = records["v"].reshape(-1, 3).astype(np.float64)
    vertices, index = np.unique(np.round(corners, 5), axis=0, return_inverse=True)
    return vertices, index.reshape(-1, 3)


def object_model(vertices, triangles, object_id):

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        ' <resources>',
        f'  <object id="{object_id}" p:UUID="{uuid.uuid4()}" type="model">',
        '   <mesh>',
        '    <vertices>',
    ]
    lines += [f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>' for x, y, z in vertices]
    lines += ['    </vertices>', '    <triangles>']
    lines += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles]
    lines += ['    </triangles>', '   </mesh>', '  </object>', ' </resources>', ' <build/>', '</model>']
    return "\n".join(lines)


# ============================================================
# PROJECT FILE
# ============================================================

def write_project(stls, out, settings, plate_name):
    """The STLs side by side (along Y), centred on plate 1."""

    parts = []
    for stl in stls:
        vertices, triangles = read_stl(stl)
        lo, hi = vertices.min(axis=0), vertices.max(axis=0)
        centre = (lo + hi) / 2.0
        parts.append((stl, vertices - centre, triangles, hi - lo))

    total = sum(size[1] for *_, size in parts) + GAP * (len(parts) - 1)
    y = BED_CENTRE[1] - total / 2.0

    objects, items, plate_items, assemble, files_objects, rels = [], [], [], [], {}, []
    for index, (stl, vertices, triangles, size) in enumerate(parts, start=1):
        mesh_id, object_id = 2 * index - 1, 2 * index
        y_mid = y + size[1] / 2.0
        y += size[1] + GAP
        place = f"1 0 0 0 1 0 0 0 1 {BED_CENTRE[0]:g} {y_mid:.6g} {size[2] / 2.0:.6g}"
        path = f"/3D/Objects/object_{index}.model"
        files_objects[path[1:]] = object_model(vertices, triangles, mesh_id)
        rels.append(f' <Relationship Target="{path}" Id="rel-{index}" '
                    f'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        objects.append(
            f'  <object id="{object_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
            f'   <components>\n'
            f'    <component p:path="{path}" objectid="{mesh_id}" p:UUID="{uuid.uuid4()}" '
            f'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
            f'   </components>\n'
            f'  </object>')
        items.append(f'  <item objectid="{object_id}" p:UUID="{uuid.uuid4()}" '
                     f'transform="{place}" printable="1"/>')
        name = stl.name
        plate_items.append(f"""  <object id="{object_id}">
    <metadata key="name" value="{name}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(triangles)}"/>
    <part id="{mesh_id}" subtype="normal_part">
      <metadata key="name" value="{name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="{name}"/>
      <metadata key="source_object_id" value="{index - 1}"/>
      <metadata key="source_volume_id" value="0"/>
      <mesh_stat face_count="{len(triangles)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>""")
        assemble.append(f'   <assemble_item object_id="{object_id}" instance_id="0" '
                        f'transform="{place}" offset="0 0 0" />')

    instances = "\n".join(f"""    <model_instance>
      <metadata key="object_id" value="{2 * i}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{100 + i}"/>
    </model_instance>""" for i in range(1, len(parts) + 1))

    main_model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">{APPLICATION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{out.stem}</metadata>
 <resources>
{chr(10).join(objects)}
 </resources>
 <build p:UUID="{uuid.uuid4()}">
{chr(10).join(items)}
 </build>
</model>
"""

    model_settings = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
{chr(10).join(plate_items)}
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="{plate_name}"/>
    <metadata key="locked" value="false"/>
{instances}
  </plate>
  <assemble>
{chr(10).join(assemble)}
  </assemble>
</config>
"""

    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>""",
        "3D/_rels/3dmodel.model.rels": '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            + "\n".join(rels) + "\n</Relationships>",
        "3D/3dmodel.model": main_model,
        **files_objects,
        "Metadata/model_settings.config": model_settings,
        "Metadata/project_settings.config": json.dumps(settings, indent=4),
        "Metadata/slice_info.config": """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="02.08.02.61"/>
  </header>
</config>""",
    }

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, text in files.items():
            archive.writestr(path, text)

    print(f"  {out.relative_to(HERE)}  ({', '.join(s.name for s in stls)})")


def main():

    tpu = HERE / "bambu" / "tpu90a_boot.json"
    petg = HERE / "bambu" / "petg_pod.json"
    jobs = [
        ([HERE / "c3pal_boot.stl"], HERE / "c3pal_boot.3mf", tpu),
        ([HERE / "c3pal_pod.stl", HERE / "c3pal_pod_lid.stl"], HERE / "c3pal_pod.3mf", petg),
        (sorted((HERE / "fit_test").glob("fit_*.stl")), HERE / "fit_test" / "fit_test.3mf", tpu),
    ]
    for stls, out, overrides in jobs:
        missing = [s for s in stls if not s.exists()]
        if not stls or missing:
            print(f"  skipped {out.name}: run generate.py / fit_test.py first")
            continue
        settings, plate_name = project_settings(overrides)
        write_project(stls, out, settings, plate_name)


if __name__ == "__main__":
    main()
