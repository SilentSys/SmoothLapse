import matplotlib.pyplot as plt
import cv2
import threading
from enum import Enum


class State(Enum):
    ready = 1
    calculating = 2
    done = 3


class TimeLapse:
    m_path = None
    m_greyFrames = []
    m_resultIndexes = []
    m_frameRate = None

    m_lock = threading.RLock()
    m_progress = 0  # lock required
    m_state = None  # lock required

    mk_threshold = None

    def __init__(self, path, threshold=100):
        self.m_path = path
        self.mk_threshold = threshold

        self.Read_()

        self.m_state = State.ready

    def Smooth(self, groupSize, lookback, blocking=True):
        with self.m_lock:  # Locking the mutex while calculating would block getProgress
            if self.m_state is State.calculating:
                raise Exception("Invalid in this state")

            if groupSize < 2:
                raise Exception("Invalid groupSize")

            if lookback < 1:
                raise Exception("Invalid lookback")

            self.m_state = State.calculating

        t = threading.Thread(target=self.Smooth_, args=(groupSize, lookback))
        t.start()
        if blocking:
            t.join()
        else:
            pass

    def Smooth_(self, groupSize, lookback):
        best = []
        minDiff = None
        for i in range(groupSize):
            hist, diff = self.Recurse_(groupSize, lookback, i, [],
                                       0)  # TODO: This can be parallelized. Should use processes, not threads to avoid GIL
            if minDiff is None or diff < minDiff:  # TODO: Handle two minimums?
                minDiff = diff  # TODO: "diff" is lookback only. At this point, we can lookforward too. Calc lookforward here to make a better decision?
                best = hist

        self.m_resultIndexes = best

        with self.m_lock:
            self.m_state = State.done

    def getProgress(self):
        with self.m_lock:
            if self.m_state is not State.calculating:
                raise Exception("Invalid in this state")

            return self.m_progress

    def isDone(self):
        with self.m_lock:
            return self.m_state is State.done

    def SaveResult(self, file):
        with self.m_lock:
            if self.m_state is not State.done:
                raise Exception("Invalid in this state")

            if not self.m_resultIndexes:
                raise Exception("No result to save")

            cap = cv2.VideoCapture(self.m_path)
            ret, frame = cap.read()
            colorIdx = 0

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            shape = frame.shape
            out = cv2.VideoWriter(file, fourcc, self.m_frameRate, (shape[1], shape[0]))
            for i in self.m_resultIndexes:
                while colorIdx < i:
                    ret, frame = cap.read()
                    colorIdx += 1

                out.write(frame)

            out.release()

    def PlotResultDiff(self):
        with self.m_lock:
            if self.m_state is not State.done:
                raise Exception("Invalid in this state")

            vals = []

            for i in range(len(self.m_resultIndexes)):
                if i == 0:
                    # first frame
                    vals.append(self.Diff_(self.m_resultIndexes[0], self.m_resultIndexes[1]) * 2)

                elif i == len(self.m_resultIndexes) - 1:
                    # last frame
                    vals.append(self.Diff_(self.m_resultIndexes[len(self.m_resultIndexes) - 1],
                                           self.m_resultIndexes[len(self.m_resultIndexes) - 2]) * 2)

                else:
                    vals.append(self.Diff_(self.m_resultIndexes[i], self.m_resultIndexes[i + 1]) +
                                self.Diff_(self.m_resultIndexes[i], self.m_resultIndexes[i - 1]))  # should we really go both ways?

            plt.plot(vals)
            plt.ylabel('some numbers')
            plt.show()  # TODO: Plot should not be continuous (dots not lines)

    def ShowResultDiff(self, threshold):
        with self.m_lock:
            if self.m_state is not State.done:
                raise Exception("Invalid in this state")

            for i in range(len(self.m_resultIndexes)):
                if i != self.m_resultIndexes[0]:
                    diff = cv2.absdiff(self.m_greyFrames[self.m_resultIndexes[i]], self.m_greyFrames[self.m_resultIndexes[i - 1]])  # Duplicate from Diff_
                    ret, diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

                    cv2.imshow('frame', diff)

                    if cv2.waitKey(0) & 0xFF == ord('q'):
                        break

        cv2.destroyAllWindows()

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

        with self.m_lock:
            self.m_progress += 100 / len(self.m_greyFrames)

        return self.Recurse_(groupSize, lookback, minDiffIdx, hist,
                             diff)  # TODO: Only called once, not real recursion. Switch to loop

    def Read_(self):
        cap = cv2.VideoCapture(self.m_path)

        self.m_frameRate = cap.get(cv2.CAP_PROP_FPS)

        while (cap.isOpened()):  # TODO: Can this be parallelized? Pipelined?
            ret, frame = cap.read()

            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.resize(frame, (100, 100))
            self.m_greyFrames.append(frame)

        cap.release()

    def Diff_(self, A, B):
        diff = cv2.absdiff(self.m_greyFrames[A], self.m_greyFrames[B])
        ret, thresh = cv2.threshold(diff, self.mk_threshold, 1, cv2.THRESH_BINARY)
        sum = cv2.sumElems(thresh)[0]
        return sum
