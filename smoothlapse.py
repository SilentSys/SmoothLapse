import argparse
from timelapse import TimeLapse
import time

parser = argparse.ArgumentParser()

parser.add_argument("input", type=str, help="Input video file")
parser.add_argument("output", type=str, help="Output video file")
parser.add_argument("groupSize", type=int, help="Frame group size")
parser.add_argument("lookback", type=int, help="Frame lookback")
parser.add_argument("-t", "--threshold", type=int, help="Diff threshold",)

args = parser.parse_args()

print("Loading video...")
if args.threshold:
    t = TimeLapse(args.input, threshold=args.threshold)
else:
    t = TimeLapse(args.input)

print("Calculating smooth timelapse...")
t.Smooth(args.groupSize, args.lookback, blocking=False)

while not t.isDone():
    progress = t.getProgress()
    print('\r[%s%s] %.2f%%' % ('#' * int(progress / 100 * 20), ' ' * (20 - int(progress / 100 * 20)), progress), end="\r")
    time.sleep(0.5)
print("\n", end="")

print("Saving to file...")
t.SaveResult(args.output)

print("Done.")
