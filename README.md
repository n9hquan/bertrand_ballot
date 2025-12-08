# Bertrand Ballot Visualizer

Simple PyQt6 + matplotlib app that animates the ballot counting process
and visualizes the lead A - B. The line is colored:

- Blue when A leads
- Red when B leads
- Gray for ties, and a faint vertical mark at tie steps

## How to use

User sets A and B totals, hits
"Run Animation", and sees the animation. Theoretical probability
P = (a - b) / (a + b) is shown.

## Command

Run:

```bash
pip install -r requirements.txt
python main.py
```
