import detail

class Calculator:

    def __init__(self, groupSize, lookback, idx, buffer, threshold):
        self.hist = []
        self.frameCache = []
        self.diff = 0
        self.idx = None

        self.done = False

        self.groupSize = groupSize
        self.lookback = lookback
        self.idx = idx
        self.buffer = buffer # TODO: Should be passing in just the consumer, not buffer. Maybe get rid of consumer model
        self.consumer = buffer.getConsumer()
        self.threshold = threshold


    def Calculate(self):
        if self.done:
            raise Exception("Calculator already done")

        assert self.idx >= len(self.hist) * self.groupSize

        self.hist.append(self.idx)
        self.frameCache.append(self.consumer.getFrame(self.idx))
        while len(self.frameCache) > self.lookback:
            del self.frameCache[0]

        startIdx = len(self.hist) * self.groupSize

        if startIdx + self.groupSize > self.buffer.getFrameCount():  # TODO: Consider ways of handling remainder frames
            self.done = True
            return True

        minDiffIdx = None
        minDiff = None
        for i in range(self.groupSize):
            iidx = startIdx + i
            idiff = 0

            for f in self.frameCache:
                idiff += detail.Diff(self.consumer.getFrame(iidx), f, self.threshold)

            if minDiff is None or idiff < minDiff:
                minDiffIdx = iidx
                minDiff = idiff

        self.diff += minDiff
        self.idx = minDiffIdx

        return False
