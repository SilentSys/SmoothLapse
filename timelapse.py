import matplotlib.pyplot as plt
import cv2


class TimeLapse:
    m_colorFrames = []
    m_greyFrames = []
    m_resultIndexes = []
    m_frameRate = None

    mk_threshold = 100  # TODO: Adjustable?

    def __init__(self, path):
        self.Read_(path)

    def Smooth(self, groupSize, lookback):
        if groupSize < 2:
            raise Exception("Invalid groupSize")

        if lookback < 1:
            raise Exception("Invalid lookback")

        best = []
        minDiff = None
        for i in range(groupSize):
            hist, diff = self.Recurse_(groupSize, lookback, i, [], 0)  # TODO: This can be parallelized.
            if minDiff is None or diff < minDiff:  # TODO: Handle two minimums?
                minDiff = diff  # TODO: "diff" is lookback only. At this point, we can lookforward too. Calc lookforward here to make a better decision?
                best = hist

        self.m_resultIndexes = best

    def SaveResult(self, file):
        if not self.m_resultIndexes:
            raise Exception("No result to save")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        shape = self.m_colorFrames[0].shape
        out = cv2.VideoWriter(file, fourcc, self.m_frameRate, (shape[1], shape[0]))
        for i in self.m_resultIndexes:
            out.write(self.m_colorFrames[i])

        out.release()

    def PlotResultDiff(self):
        vals = []

        for i in self.m_resultIndexes:
            if i == self.m_resultIndexes[0]:
                # first frame
                vals.append(self.Diff_(self.m_resultIndexes[0], self.m_resultIndexes[1]) * 2)
                continue

            if i == self.m_resultIndexes[len(self.m_resultIndexes) - 1]:
                # last frame
                vals.append(self.Diff_(self.m_resultIndexes[len(self.m_resultIndexes) - 1],
                                       self.m_resultIndexes[len(self.m_resultIndexes) - 2]) * 2)
                continue

            vals.append(self.Diff_(i, i + 1) + self.Diff_(i, i - 1))

        plt.plot(vals)
        plt.ylabel('some numbers')
        plt.show()  # TODO: Plot should not be continuous (dots not lines)

    def Prune(self, threshold):
        raise Exception("Not implemented") # TODO

    def Recurse_(self, groupSize, lookback, idx, hist, diff):
        assert idx >= len(hist) * groupSize

        hist.append(idx)

        startIdx = len(hist) * groupSize

        if startIdx + groupSize - 1 >= len(
                self.m_greyFrames):  # TODO: Consider ways of handling remainder frames
            return hist, diff

        minDiffIdx = None
        minDiff = None
        for i in range(groupSize):
            iidx = startIdx + i
            idiff = 0

            for l in range(lookback):
                back = len(hist) - 1 - l
                if back < 0:
                    break
                idiff += self.Diff_(iidx, hist[back])

            if minDiff is None or idiff < minDiff:  # TODO: Handle branching in case of two minimums?
                minDiffIdx = iidx
                minDiff = idiff

        diff += minDiff
        return self.Recurse_(groupSize, lookback, minDiffIdx, hist, diff)  # Only called once, not real recursion. Maybe once we branch or do multiple passes

    def Read_(self, path):
        cap = cv2.VideoCapture(path)

        self.m_frameRate = cap.get(cv2.CAP_PROP_FPS)

        while (cap.isOpened()):  # TODO: Can this be parallelized? At least the conversion to greyscale
            ret, frame = cap.read()

            if not ret:
                break

            self.m_colorFrames.append(frame)
            self.m_greyFrames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    def Diff_(self, A, B):
        diff = cv2.absdiff(self.m_greyFrames[A], self.m_greyFrames[B])
        ret, thresh = cv2.threshold(diff, self.mk_threshold, 1, cv2.THRESH_BINARY)
        sum = cv2.sumElems(thresh)[0]
        return sum
