# Bertrand Ballot Visualizer

Simple PyQt6 + matplotlib app that animates the ballot counting process
and visualizes the lead A - B. The line is colored piecewise:

- Blue when A leads (y > 0)
- Red when B leads (y < 0)
- Gray for ties (y == 0), plus a faint vertical mark at tie steps

The UI is intentionally minimal: user sets A and B totals, hits
"Run Single (Animate)", and sees the animation. Theoretical probability
P = (a - b) / (a + b) is shown (0 if a <= b).

Run:

```bash
pip install -r requirements.txt
python main.py
```
