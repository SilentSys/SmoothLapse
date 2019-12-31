import argparse
from timelapse import TimeLapse
import time

parser = argparse.ArgumentParser()

parser.add_argument("input", type=str, help="Input video file")
parser.add_argument("output", type=str, help="Output video file")
parser.add_argument("groupSize", type=int, help="Frame group size")
parser.add_argument("lookback", type=int, help="Frame lookback")
parser.add_argument("-t", "--threshold", type=int, help="Diff threshold")
parser.add_argument("-f", "--fps", type=int, help="Output framerate override")
parser.add_argument("-p", "--passes", type=int, help="Number of passes to perform")

args = parser.parse_args()

print("Starting...")
if args.threshold:
    t = TimeLapse(args.input, threshold=args.threshold)
else:
    t = TimeLapse(args.input)

print("Calculating smooth timelapse...")
if args.passes:
    t.Smooth(args.groupSize, args.lookback, blocking=False, numPasses=args.passes)
else:
    t.Smooth(args.groupSize, args.lookback, blocking=False)

while True:
    progress = t.getProgress()
    print('\r[%s%s] %.2f%%' % ('#' * int(progress / 100 * 20), ' ' * (20 - int(progress / 100 * 20)), progress), end="\r")
    if t.isDone():
        break
    time.sleep(0.5)
print("\n", end="")

print("Saving to file...")
if args.fps:
    t.SaveResult(args.output, args.fps)
else:
    t.SaveResult(args.output)

print("Done.")
