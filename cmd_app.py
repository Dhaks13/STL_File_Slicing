import os
import trimesh
import numpy as np
import matplotlib.pyplot as plt


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

        for ent in slice2D.entities:
            pts = ent.discrete(verts_s)
            if len(pts) < 2:
                continue
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color='black', linewidth=1)  # Fixed color

        out_path = os.path.join(out_dir, f'layer_{i:04d}.png')
        plt.savefig(out_path, dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close(fig)


def main():
    print("Select an STL file to slice into layers.")
    file = filedialog.askopenfilename(
        title="Select STL file",
        filetypes=[("STL files", "*.stl"), ("All files", "*.*")]
    )
    if not file:
        print("No file selected.")
        return
    print("The layers will be saved as PNG images in the selected output directory.")
    print("Select the output directory where the layers will be saved.")
    out_dir = filedialog.askdirectory(
        title="Select output directory"
    )
    if not out_dir:
        print("No output directory selected.")
        return
    height = float(input("Enter layer height (default 0.05): ") or 0.05)
    print(f"Slicing {file} into layers...")
    slice_stl_to_layers(file, out_dir, layer_height=height)

if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()  # Hide the root window

    try:
        main()
        messagebox.showinfo("Success", "Layers generated successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))    
