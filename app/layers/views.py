import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt

from django.shortcuts import render, redirect
from django.conf import settings


def slice_stl_to_layers(stl_path, out_dir, layer_height=0.05, canvas_size=1024, margin=50):
    os.makedirs(out_dir, exist_ok=True)
    mesh = trimesh.load_mesh(stl_path)

    padding = 0.01
    line_radius = 0.1
    bounds = mesh.bounds
    x_min, y_min, z_min = bounds[0]
    x_max, y_max, z_max = bounds[1]

    corners = [
    [x_min - padding, y_min - padding],
    [x_max + padding, y_min - padding],
    [x_max + padding, y_max + padding],
    [x_min - padding, y_max + padding]
    ]
    lines = []
    for x, y in corners:
      start = np.array([x, y, z_min])
      end = np.array([x, y, z_max])
      line = trimesh.creation.cylinder(
        radius=line_radius,
        segment=[start, end],
        sections=12
      )
      lines.append(line)

    all_lines = trimesh.util.concatenate(lines)
    combined_mesh = trimesh.util.concatenate([mesh, all_lines])
    mesh = combined_mesh

    z_min, z_max = mesh.bounds[:, 2]
    num_layers = int(np.ceil((z_max - z_min) / layer_height))

    region_colors = {
        'inskin': 'blue', 'downskin': 'red', 'upskin': 'yellow',
        'support': 'gray', 'highlight': 'green', 'dummy': 'black'
    }
    region_tags = list(region_colors)

    for i in range(num_layers):
        z = z_min + i * layer_height
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if section is None:
            continue
        slice2D, _ = section.to_2D()
        verts = slice2D.vertices

        # Scale and center
        xy_min, xy_max = verts.min(0), verts.max(0)
        center = (xy_min + xy_max) / 2
        span = np.linalg.norm(xy_max - xy_min) / 2
        base_radius = (canvas_size - 2 * margin) / 2
        scale = base_radius / span if span else 1
        verts_s = (verts - center) * scale + canvas_size // 2

        # Draw
        fig, ax = plt.subplots(figsize=(canvas_size / 100, canvas_size / 100), dpi=100)
        ax.set_xlim(0, canvas_size)
        ax.set_ylim(0, canvas_size)
        ax.axis('off')
        ax.set_aspect('equal')
        circle = plt.Circle((canvas_size // 2, canvas_size // 2), base_radius,
                            fill=False, linestyle='--', linewidth=1, color='lightgray')
        ax.add_artist(circle)

        for j, ent in enumerate(slice2D.entities):
            pts = ent.discrete(verts_s)
            if len(pts) < 2:
                continue
            tag = region_tags[j % len(region_tags)]
            color = region_colors[tag]
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=color, linewidth=1)

        out_path = os.path.join(out_dir, f'layer_{i:04d}.png')
        plt.savefig(out_path, dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close(fig)


def layer_view(request):
    if request.method == 'POST':
        # --- Clear old layers ---
        layers_dir = os.path.join(settings.MEDIA_ROOT, 'layers')
        if os.path.isdir(layers_dir):
            for fname in os.listdir(layers_dir):
                fpath = os.path.join(layers_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
        else:
            os.makedirs(layers_dir)

        # Save new STL upload
        uploaded = request.FILES['file']
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        stl_path = os.path.join(upload_dir, uploaded.name)
        with open(stl_path, 'wb') as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        # Slice into fresh layers
        slice_stl_to_layers(stl_path, layers_dir)

        return redirect('layers')
    layers_dir = os.path.join(settings.MEDIA_ROOT, 'layers')
    filenames = sorted(f for f in os.listdir(layers_dir) if f.endswith('.png'))
    files = [
        {'name': name, 'url': settings.MEDIA_URL + 'layers/' + name}
        for name in filenames
    ]
    return render(request, 'layers.html', {'files': files})
