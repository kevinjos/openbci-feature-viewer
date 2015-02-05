import numpy as np
from itertools import count, imap
from vispy import app, scene
from vispy.util.filter import gaussian_filter
from collections import deque
import threading

canvas = scene.SceneCanvas(keys='interactive')
view = canvas.central_widget.add_view()
view.set_camera('turntable', mode='perspective', up='z', distance=2,
                azimuth=30., elevation=30.)

## Simple surface plot example
## x, y values are not specified, so assumed to be 0:50
#z = gaussian_filter(np.random.normal(size=(50, 50)), (1, 1)) * 10
z = np.array([np.array([np.random.random() for n in range(60)]) for n in range(60)])
flat_z = z.flatten()
colors = np.array(map(lambda point: np.array([1-point, point, 0, 1]), flat_z))
#p1 = scene.visuals.SurfacePlot(z=z, colors=colors)
p1 = scene.visuals.SurfacePlot(z=z)
p1.transform = scene.transforms.AffineTransform()
p1.transform.scale([1/49., 1/49., 0.2])

view.add(p1)

# Add a 3D axis to keep us oriented
axis = scene.visuals.XYZAxis(parent=view.scene)

canvas.show()

is_running = True

def run_plot(z):
    for i in range(60):
        if i == 59:
            z[i] = np.array([np.random.random() for n in range(60)])
        else:
            z[i] = z[i+1]
    flat_z = z.flatten()
    colors = np.array(map(lambda point: np.array([1-point, point, 0, 1]), flat_z))
    p1.set_data(z=z, colors=colors)
    if is_running:
        t = threading.Timer(2, run_plot, args=[z])
        t.start()

