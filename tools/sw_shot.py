"""Clean SolidWorks screenshots for the website.

usage: python sw_shot.py [--view iso|tri|dim] <in> <out.png> [<in> <out.png> ...]
  in = .SLDPRT / .SLDASM (shaded with edges) or .STL (shaded, graphics body)

Temporarily: plain white background, no origins/triad/shadows, STL -> graphics body.
Every system setting touched is restored in a finally block, even on error.
Per-document changes (hidden types, scene floor reflections) are never saved:
documents are closed without saving.
"""
import sys
import inspect
import pythoncom
import win32com.client
from win32com.client import VARIANT

VIEWS = {"iso": "*Isometric", "tri": "*Trimetric", "dim": "*Dimetric"}

# (kind, enum id, screenshot value)
SETTINGS = [
    ("tog", 6, False),        # swDisplayOrigins
    ("tog", 205, False),      # swDisplayReferenceTriad
    ("tog", 131, False),      # swDisplayShadowsInShadedMode
    ("int", 305, 0),          # swColorsBackgroundAppearance = plain
    ("int", 99, 0xFFFFFF),    # swSystemColorsViewportBackground = white
    ("int", 208, 0),          # swImportStlVrmlModelType = graphics
]


def call(obj, name, *args):
    """pywin32 late binding exposes no-arg methods as properties; handle both."""
    attr = getattr(obj, name)
    return attr(*args) if inspect.ismethod(attr) else attr


def kill_floor(doc):
    for path in (("GetActiveConfiguration", "GetScene"), ("Extension", "GetScene")):
        try:
            obj = doc
            for p in path:
                obj = call(obj, p)
            obj.FloorReflections = False
            obj.FloorShadows = False
            return ".".join(path)
        except Exception as e:
            last = e
    return f"failed: {last}"


def get(sw, kind, k):
    return sw.GetUserPreferenceToggle(k) if kind == "tog" else sw.GetUserPreferenceIntegerValue(k)


def put(sw, kind, k, v):
    if kind == "tog":
        sw.SetUserPreferenceToggle(k, v)
    else:
        sw.SetUserPreferenceIntegerValue(k, v)


def open_doc(sw, path):
    ext = path.rsplit(".", 1)[-1].lower()
    # typed wrappers return out-params as a tuple: (result, *outs)
    if ext == "stl":
        res = sw.LoadFile4(path, "", None, 0)
    else:
        res = sw.OpenDoc6(path, 2 if ext == "sldasm" else 1, 1, "", 0, 0)
    doc, *outs = res if isinstance(res, tuple) else (res,)
    return doc, ext, outs


def prep(sw, doc, ext, view, mode):
    doc.SetUserPreferenceToggle(198, True)  # hide all types (doc only)
    print("  floor:", kill_floor(doc))
    call(doc, "ActiveView").DisplayMode = mode if mode else (4 if ext == "stl" else 5)
    doc.ShowNamedView2(view, -1)
    call(doc, "ViewZoomtofit2")


def main(argv):
    view, same_scale, mode = "*Isometric", False, None
    while argv and argv[0].startswith("--"):
        if argv[0] == "--view":
            view, argv = VIEWS[argv[1]], argv[2:]
        elif argv[0] == "--same-scale":   # every image at the zoom of the largest part
            same_scale, argv = True, argv[1:]
        elif argv[0] == "--shaded":       # no edge lines (match STL graphics bodies)
            mode, argv = 4, argv[1:]
    if same_scale:
        return main_same_scale(argv, view, mode)
    sw = connect()
    orig = [(kind, k, get(sw, kind, k)) for kind, k, _ in SETTINGS]
    print("original:", orig)
    try:
        for kind, k, v in SETTINGS:
            put(sw, kind, k, v)
        for src, out in zip(argv[0::2], argv[1::2]):
            doc, ext, err = open_doc(sw, src)
            if doc is None:
                print("open failed:", src, "err", err)
                continue
            try:
                doc.SetUserPreferenceToggle(198, True)  # hide all types (doc only)
                prep(sw, doc, ext, view, mode)
                call(doc, "GraphicsRedraw2")
                print(out, "->", doc.SaveAs(out))
            finally:
                sw.CloseDoc(call(doc, "GetTitle"))
    finally:
        restore(sw, orig)


def connect():
    # SolidWorks' IDispatch has no type info, so build wrappers from sldworks.tlb
    tlb = pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldworks.tlb")
    a = tlb.GetLibAttr()
    mod = win32com.client.gencache.EnsureModule(str(a[0]), a[1], a[3], a[4])
    sw = mod.ISldWorks(win32com.client.dynamic.Dispatch("SldWorks.Application")._oleobj_)
    sw.Visible = True
    return sw


def main_same_scale(argv, view, mode):
    sw = connect()
    orig = [(kind, k, get(sw, kind, k)) for kind, k, _ in SETTINGS]
    print("original:", orig)
    docs = []
    try:
        for kind, k, v in SETTINGS:
            put(sw, kind, k, v)
        # pass 1: open everything, zoom to fit, note each zoom level
        for src, out in zip(argv[0::2], argv[1::2]):
            doc, ext, _ = open_doc(sw, src)
            if doc is None:
                print("open failed:", src)
                continue
            docs.append((doc, out))
            prep(sw, doc, ext, view, mode)
        scales = [call(d, "ActiveView").Scale2 for d, _ in docs]
        s = min(scales)
        print("zoom levels:", [round(x, 3) for x in scales], "-> using", round(s, 3))
        # pass 2: same zoom for all, then save
        for doc, out in docs:
            sw.ActivateDoc3(call(doc, "GetTitle"), False, 0, 0)
            print("  floor (active):", kill_floor(doc))  # first try can fail while several docs are loading
            call(doc, "ActiveView").Scale2 = s
            call(doc, "GraphicsRedraw2")
            print(out, "->", doc.SaveAs(out))
    finally:
        for doc, _ in docs:
            try:
                sw.CloseDoc(call(doc, "GetTitle"))
            except Exception as e:
                print("close failed:", e)
        restore(sw, orig)


def restore(sw, orig):
    for kind, k, v in orig:
        put(sw, kind, k, v)
    now = [(kind, k, get(sw, kind, k)) for kind, k, _ in SETTINGS]
    print("restored ok" if now == orig else f"RESTORE MISMATCH: {now}")


if __name__ == "__main__":
    main(sys.argv[1:])
