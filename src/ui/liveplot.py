import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import LineCollection

class LivePlot(FigureCanvas):
    """Matplotlib canvas showing piecewise-colored lead (A-B).


    Behavior summary:
    - starts at (0, 0)
    - when adding a new point, create a segment from previous to current
    point; if it crosses y=0 split segment into two and color each side
    - points colored: blue (y>0), red (y<0), gray (y==0)
    - tie points (y==0) also draw a faint vertical dashed line at that x
    """


    def __init__(self, parent=None, width=6, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Ballots counted")
        self.ax.set_ylabel("Lead (A - B)")
        self.ax.axhline(0, color="gray", linewidth=0.8)


        # storage
        self.xdata = []
        self.ydata = []
        self.segments = []
        self.colors = []


        self.lc = LineCollection([], linewidths=2, zorder=2)
        self.ax.add_collection(self.lc)


        self.scatter = self.ax.scatter([], [], s=36, zorder=3)


        # legend
        self.ax.plot([], [], color="blue", label="A leading")
        self.ax.plot([], [], color="red", label="B leading")
        self.ax.plot([], [], color="gray", label="Tie")
        self.ax.legend(loc="upper right")


        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(-1, 1)
        self.fig = fig


    def reset(self, n_steps: int):
        """Reset plot and start from (0, 0)."""
        self.xdata = [0]
        self.ydata = [0]
        self.segments = []
        self.colors = []
        self.lc.set_segments([])
        self.lc.set_color([])


        self.scatter.set_offsets(np.array([[0, 0]]))
        self.scatter.set_facecolors(["gray"])
        self.scatter.set_edgecolors(["gray"])


        self.ax.set_xlim(0, max(1, n_steps))
        self.ax.set_ylim(-max(1, n_steps // 2), max(1, n_steps // 2))
        self.draw()
        
    def _add_segment_with_color(self, seg, color):
        self.segments.append(seg)
        self.colors.append(color)
        self.lc.set_segments(self.segments)
        self.lc.set_color(self.colors)
        
    def add_point(self, step: int, lead: int):
        """Add a new point at x=step, y=lead and update segments/points.
        step should be an integer (number of ballots counted so far).
        """
        self.xdata.append(step)
        self.ydata.append(lead)


        # update scatter (point markers)
        pts = np.column_stack((self.xdata, self.ydata))
        point_colors = ["blue" if y > 0 else ("red" if y < 0 else "gray") for y in self.ydata]
        self.scatter.set_offsets(pts)
        self.scatter.set_facecolors(point_colors)
        self.scatter.set_edgecolors(point_colors)


        # if tie at this step, draw faint vertical line
        if lead == 0:
            # small zorder so the line is under markers but visible
            self.ax.axvline(x=step, color="gray", linestyle="--", alpha=0.35, zorder=1)


        if len(self.xdata) >= 2:
            x0, y0 = self.xdata[-2], self.ydata[-2]
            x1, y1 = self.xdata[-1], self.ydata[-1]


        # both above
        if y0 > 0 and y1 > 0:
            self._add_segment_with_color([(x0, y0), (x1, y1)], "blue")
        # both below
        elif y0 < 0 and y1 < 0:
            self._add_segment_with_color([(x0, y0), (x1, y1)], "red")
        # both tie
        elif y0 == 0 and y1 == 0:
            self._add_segment_with_color([(x0, y0), (x1, y1)], "gray")
        else:
            # crossing case — split at y=0
            # compute fraction t where y = 0 between the two points
            # t in (0,1)
            t = (0 - y0) / (y1 - y0)
            xc = x0 + t * (x1 - x0)
            seg1 = [(x0, y0), (xc, 0.0)]
            seg2 = [(xc, 0.0), (x1, y1)]
            c1 = "blue" if y0 > 0 else ("red" if y0 < 0 else "gray")
            c2 = "blue" if y1 > 0 else ("red" if y1 < 0 else "gray")
            self._add_segment_with_color(seg1, c1)
            self._add_segment_with_color(seg2, c2)


        # autoscale y-range if needed
        ymin, ymax = self.ax.get_ylim()
        absmax = max(abs(ymin), abs(ymax), abs(lead))
        if abs(lead) >= max(abs(ymin), abs(ymax)) - 1:
            new = max(5, absmax * 1.3)
            self.ax.set_ylim(-new, new)


        self.ax.set_xlim(0, max(10, step + 1))
        self.draw()