
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from itertools import permutations
# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="PackWise",
    layout="wide"
)

st.title("📦 PackWise-3D Box Fitness Checker")

st.write(
    "Automatically finds the best rotation "
    "to fit the package inside the bin."
)

# =========================================================
# SIDEBAR INPUTS
# =========================================================

st.sidebar.header("Bin Dimensions")

bin_l = st.sidebar.number_input(
    "Bin Length",
    min_value=1.0,
    value=10.0
)

bin_b = st.sidebar.number_input(
    "Bin Breadth",
    min_value=1.0,
    value=8.0
)

bin_h = st.sidebar.number_input(
    "Bin Height",
    min_value=1.0,
    value=6.0
)

# =========================================================
# PACKAGE INPUTS
# =========================================================

st.sidebar.header("Package Dimensions")

pkg_l = st.sidebar.number_input(
    "Package Length",
    min_value=1.0,
    value=11.0
)

pkg_b = st.sidebar.number_input(
    "Package Breadth",
    min_value=1.0,
    value=7.0
)

pkg_h = st.sidebar.number_input(
    "Package Height",
    min_value=1.0,
    value=5.0
)

# =========================================================
# SEARCH SETTINGS
# =========================================================

st.sidebar.header("Search Settings")

rotation_step = st.sidebar.slider(
    "Rotation Precision (degrees)",
    5,
    45,
    15
)

# =========================================================
# CREATE BOX VERTICES
# =========================================================

def create_vertices(l, b, h):

    x = l / 2
    y = b / 2
    z = h / 2

    vertices = np.array([
        [-x, -y, -z],
        [-x, -y,  z],
        [-x,  y, -z],
        [-x,  y,  z],
        [ x, -y, -z],
        [ x, -y,  z],
        [ x,  y, -z],
        [ x,  y,  z]
    ])

    return vertices

# =========================================================
# ROTATION MATRIX
# =========================================================

def rotation_matrix(ax, ay, az):

    ax = np.radians(ax)
    ay = np.radians(ay)
    az = np.radians(az)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(ax), -np.sin(ax)],
        [0, np.sin(ax),  np.cos(ax)]
    ])

    Ry = np.array([
        [ np.cos(ay), 0, np.sin(ay)],
        [0, 1, 0],
        [-np.sin(ay), 0, np.cos(ay)]
    ])

    Rz = np.array([
        [np.cos(az), -np.sin(az), 0],
        [np.sin(az),  np.cos(az), 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx

# =========================================================
# BOX EDGES
# =========================================================

def get_box_edges(vertices):

    edges = [
        (0,1),(0,2),(0,4),
        (1,3),(1,5),
        (2,3),(2,6),
        (3,7),
        (4,5),(4,6),
        (5,7),
        (6,7)
    ]

    lines = []

    for edge in edges:

        start = vertices[edge[0]]
        end = vertices[edge[1]]

        lines.append(start)
        lines.append(end)
        lines.append([None, None, None])

    return np.array(lines, dtype=object)

# =========================================================
# FAST FIT SEARCH
# =========================================================


def find_simple_fit(bin_l, bin_b, bin_h, pkg_l, pkg_b, pkg_h):

    for dims in set(permutations([pkg_l, pkg_b, pkg_h])):

        w, d, h = dims

        if (
            w <= bin_l and
            d <= bin_b and
            h <= bin_h
        ):
            return True, dims

    return False, None
def auto_find_fit(
    bin_l,
    bin_b,
    bin_h,
    pkg_vertices,
    rotation_step
):

    best_volume = float("inf")

    best_package = None
    best_angles = None
    best_dims = None

    # SEARCH ROTATIONS
    for ax in range(0, 181, rotation_step):

        for ay in range(0, 181, rotation_step):

            for az in range(0, 181, rotation_step):

                # ROTATE PACKAGE
                R = rotation_matrix(ax, ay, az)

                rotated = pkg_vertices @ R.T

                # GET ROTATED BOUNDING SIZE
                xs = rotated[:, 0]
                ys = rotated[:, 1]
                zs = rotated[:, 2]

                width = xs.max() - xs.min()
                depth = ys.max() - ys.min()
                height = zs.max() - zs.min()

                # CHECK FIT
                if (
                    width <= bin_l and
                    depth <= bin_b and
                    height <= bin_h
                ):

                    # FIND UNUSED VOLUME
                    unused_volume = (
                        (bin_l * bin_b * bin_h)
                        -
                        (width * depth * height)
                    )

                    # SAVE BEST FIT
                    if unused_volume < best_volume:

                        best_volume = unused_volume
                        best_package = rotated
                        best_angles = (ax, ay, az)
                        best_dims = (width, depth, height)

    # NO FIT FOUND
    if best_package is None:

        return (
            False,
            pkg_vertices,
            None,
            None
        )

    return (
        True,
        best_package,
        best_angles,
        best_dims
    )

# =========================================================
# CREATE BIN + PACKAGE
# =========================================================

bin_vertices = create_vertices(
    bin_l,
    bin_b,
    bin_h
)

pkg_vertices = create_vertices(
    pkg_l,
    pkg_b,
    pkg_h
)

# =========================================================
# RUN SEARCH
# =========================================================
with st.spinner("Finding best rotation..."):

    simple_fit, simple_dims = find_simple_fit(
        bin_l,
        bin_b,
        bin_h,
        pkg_l,
        pkg_b,
        pkg_h
    )

    if simple_fit:

        fits = True

        w, d, h = simple_dims

        fitted_package = create_vertices(
            w,
            d,
            h
        )

        best_angles = (0, 0, 0)

        best_dims = (
            w,
            d,
            h
        )

    else:

        fits, fitted_package, best_angles, best_dims = auto_find_fit(
            bin_l,
            bin_b,
            bin_h,
            pkg_vertices,
            rotation_step
        )

# =========================================================
# RESULTS
# =========================================================

st.subheader("📊 Fit Result")

if fits:

    st.success("✅ Package FITS inside the bin")

    col1, col2 = st.columns(2)

    with col1:

        st.write("### Best Rotation")

        st.write(f"Rotate X: {best_angles[0]}°")
        st.write(f"Rotate Y: {best_angles[1]}°")
        st.write(f"Rotate Z: {best_angles[2]}°")

    with col2:

        st.write("### Occupied Dimensions")

        st.write(f"Width: {best_dims[0]:.2f}")
        st.write(f"Depth: {best_dims[1]:.2f}")
        st.write(f"Height: {best_dims[2]:.2f}")

else:

    st.error("❌ Package DOES NOT fit")

# =========================================================
# CENTER PACKAGE
# =========================================================

if fits:

    min_x = fitted_package[:, 0].min()
    min_y = fitted_package[:, 1].min()
    min_z = fitted_package[:, 2].min()

    fitted_package += np.array([
        (-bin_l / 2) - min_x,
        (-bin_b / 2) - min_y,
        (-bin_h / 2) - min_z
    ])

# =========================================================
# CREATE EDGES
# =========================================================

bin_edges = get_box_edges(bin_vertices)
pkg_edges = get_box_edges(fitted_package)

# =========================================================
# CREATE FIGURE
# =========================================================

fig = go.Figure()

# BIN
fig.add_trace(go.Scatter3d(
    x=bin_edges[:, 0],
    y=bin_edges[:, 1],
    z=bin_edges[:, 2],
    mode='lines',
    name='Bin',
    line=dict(width=6)
))

# PACKAGE
fig.add_trace(go.Scatter3d(
    x=pkg_edges[:, 0],
    y=pkg_edges[:, 1],
    z=pkg_edges[:, 2],
    mode='lines',
    name='Package',
    line=dict(width=6)
))

# =========================================================
# LAYOUT
# =========================================================

fig.update_layout(
    height=800,

    scene=dict(
        xaxis_title='X',
        yaxis_title='Y',
        zaxis_title='Z',
        aspectmode='data'
    ),

    margin=dict(
        l=0,
        r=0,
        b=0,
        t=40
    )
)

# =========================================================
# SHOW FIGURE
# =========================================================

st.plotly_chart(
    fig,
    use_container_width=True
)

