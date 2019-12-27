import argparse
from timelapse import TimeLapse

parser = argparse.ArgumentParser()

parser.add_argument("input", type=str, help="Input video file")
parser.add_argument("output", type=str, help="Output video file")
parser.add_argument("groupSize", type=int, help="Frame group size")
parser.add_argument("lookback", type=int, help="Frame lookback")

args = parser.parse_args()

t = TimeLapse(args.input)
t.Smooth(args.groupSize, args.lookback)
t.SaveResult(args.output)

print("Done.")
