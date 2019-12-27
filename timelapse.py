import matplotlib.pyplot as plt
import cv2


class TimeLapse:
    m_path = None;
    m_colorFrames = []
    m_greyFrames = []
    m_smoothIndexes = []
    m_groupSize = None
    m_lookback = None
    mk_threshold = 100  # TODO: Adjustable?

    def __init__(self, path, groupSize, lookback):
        self.m_path = path
        self.m_groupSize = groupSize
        self.m_lookback = lookback

        self.Read_()

    def Calculate(self):
        best = []
        minDiff = None
        for i in range(self.m_groupSize):
            hist, diff = self.Recurse_(i, [], 0) # TODO: This can be parallelized.
            if minDiff is None or diff < minDiff:  # TODO: Handle two minimums?
                minDiff = diff  # TODO: "diff" is lookback only. At this point, we can lookforward too. Calc lookforward here to make a better decision?
                best = hist

        self.m_smoothIndexes = best

    def Save(self, file):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        shape = self.m_colorFrames[0].shape
        out = cv2.VideoWriter(file, fourcc, 25.0, (shape[1], shape[0]))  # TODO: Get original framerate
        for i in self.m_smoothIndexes:
            out.write(self.m_colorFrames[i])

        out.release()

    def PlotResults(self):
        vals = []

        for i in self.m_smoothIndexes:
            if i == self.m_smoothIndexes[0]:
                # first frame
                vals.append(self.Diff_(self.m_smoothIndexes[0], self.m_smoothIndexes[1]) * 2)
                continue

            if i == self.m_smoothIndexes[len(self.m_smoothIndexes) - 1]:
                # last frame
                vals.append(self.Diff_(self.m_smoothIndexes[len(self.m_smoothIndexes) - 1],
                                       self.m_smoothIndexes[len(self.m_smoothIndexes) - 2]) * 2)
                continue

            vals.append(self.Diff_(i, i + 1) + self.Diff_(i, i - 1))

        plt.plot(vals)
        plt.ylabel('some numbers')
        plt.show()  # TODO: Plot should not be continuous (dots not lines)

    def prune(self, threshold):
        pass  # TODO

    def Recurse_(self, idx, hist, diff):
        assert idx >= len(hist) * self.m_groupSize

        hist.append(idx)

        startIdx = len(hist) * self.m_groupSize

        if startIdx + self.m_groupSize - 1 >= len(
                self.m_greyFrames):  # TODO: Consider ways of handling remainder frames
            return hist, diff

        minDiffIdx = None
        minDiff = None
        for i in range(self.m_groupSize):
            iidx = startIdx + i
            idiff = 0

            for l in range(self.m_lookback):
                back = len(hist) - 1 - l
                if back < 0:
                    break
                idiff += self.Diff_(iidx, hist[back])

            if minDiff is None or idiff < minDiff:  # TODO: Handle branching in case of two minimums?
                minDiffIdx = iidx
                minDiff = idiff

        diff += minDiff
        return self.Recurse_(minDiffIdx, hist,
                             diff)  # Only called once, not real recursion. Maybe once we branch or do multiple passes

    def Read_(self):
        cap = cv2.VideoCapture(self.m_path)

        while (cap.isOpened()): # TODO: Can this be parallelized? At least the conversion to greyscale
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
