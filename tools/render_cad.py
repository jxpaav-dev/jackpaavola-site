"""Render STLs as site images.
  hero:  python render_set.py hero OUT.png elev azim file.stl
  strip: python render_set.py strip OUT.png elev azim label1=file1 label2=file2 ...
Strip renders every part at one shared scale so size changes are honest.
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

BG = "#faf8f4"
INK = "#6e6a62"
BASE = np.array([0xa39b90]).view(np.uint8)[:3][::-1] / 255.0 if False else np.array([0xa3, 0x9b, 0x90]) / 255.0
plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]


def load(p):
    m = trimesh.load(p, force="mesh")
    m.apply_translation(-m.bounds.mean(axis=0))
    return m


def draw(ax, m, r, elev, azim):
    n = m.face_normals
    e, a = np.radians(elev + 30), np.radians(azim - 40)
    light = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    fill = np.array([-light[0], -light[1], 0.3])
    fill /= np.linalg.norm(fill)
    shade = 0.55 + 0.4 * np.clip(n @ light, 0, 1) + 0.12 * np.clip(n @ fill, 0, 1)
    c = np.clip(BASE[None, :] * shade[:, None], 0, 1)
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=c, edgecolors=c, linewidths=0.25))
    ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(-r, r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor(BG)


def hero(out, elev, azim, path):
    m = load(path)
    r = (m.bounds[1] - m.bounds[0]).max() / 2 * 0.82
    fig = plt.figure(figsize=(8, 6), dpi=200, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    draw(ax, m, r, elev, azim)
    plt.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)


def strip(out, elev, azim, items):
    meshes = [(lbl, load(p)) for lbl, p in items]
    r = max((m.bounds[1] - m.bounds[0]).max() for _, m in meshes) / 2 * 0.8
    k = len(meshes)
    fig = plt.figure(figsize=(3.2 * k, 3.6), dpi=200, facecolor=BG)
    for i, (lbl, m) in enumerate(meshes):
        ax = fig.add_axes([i / k, 0.12, 1 / k, 0.88], projection="3d")
        draw(ax, m, r, elev, azim)
        fig.text((i + 0.5) / k, 0.06, lbl, ha="center", va="center", color=INK, fontsize=13)
    fig.savefig(out, facecolor=BG)


if __name__ == "__main__":
    mode, out, elev, azim = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    if mode == "each":  # out is a directory; label=file -> out/label.png, shared scale
        items = [a.split("=", 1) for a in sys.argv[5:]]
        meshes = [(l, load(p)) for l, p in items]
        r = max((m.bounds[1] - m.bounds[0]).max() for _, m in meshes) / 2 * 0.78
        for l, m in meshes:
            fig = plt.figure(figsize=(4, 4), dpi=150, facecolor=BG)
            ax = fig.add_axes([0, 0, 1, 1], projection="3d")
            draw(ax, m, r, elev, azim)
            fig.savefig(f"{out}/{l}.png", facecolor=BG)
            plt.close(fig)
        print("wrote", len(meshes))
    elif mode == "hero":
        hero(out, elev, azim, sys.argv[5])
    else:
        strip(out, elev, azim, [a.split("=", 1) for a in sys.argv[5:]])
    print("wrote", out)
