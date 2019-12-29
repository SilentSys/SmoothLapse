import matplotlib.pyplot as plt
import cv2
import threading
from enum import Enum
from framebuffer import FrameBuffer


class State(Enum):
    ready = 1
    calculating = 2
    done = 3


class TimeLapse:
    m_path = None
    m_resultIndexes = []
    m_frameRate = None
    m_numFrames = None

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

    def Smooth_(self, groupSize, lookback):
        best = []
        minDiff = None
        for i in range(groupSize):
            hist, diff = self.Calculate_(groupSize, lookback, i)  # TODO: This can be parallelized. Should use processes, not threads to avoid GIL. DONT RUN SEQUENTIALLY
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

    def SaveResult(self, file, frameRateOverride=None): # TODO: Async with progress like Smooth
        with self.m_lock:
            if self.m_state is not State.done:
                raise Exception("Invalid in this state")

            if not self.m_resultIndexes:
                raise Exception("No result to save")

            if frameRateOverride:
                frameRate = frameRateOverride
            else:
                frameRate = self.m_frameRate

            cap = cv2.VideoCapture(self.m_path)
            ret, frame = cap.read()
            colorIdx = 0

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            shape = frame.shape
            out = cv2.VideoWriter(file, fourcc, frameRate, (shape[1], shape[0]))
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
            resultFrames = self.getResultFrames_()

            for i in range(len(resultFrames)):
                if i == 0:
                    # first frame
                    vals.append(self.Diff_(resultFrames[0], resultFrames[1]) * 2)

                elif i == len(self.m_resultIndexes) - 1:
                    # last frame
                    vals.append(self.Diff_(resultFrames[len(resultFrames) - 1],
                                           resultFrames[len(resultFrames) - 2]) * 2)

                else:
                    vals.append(self.Diff_(resultFrames[i], resultFrames[i + 1]) +
                                self.Diff_(resultFrames[i], resultFrames[i - 1]))  # should we really go both ways?

            plt.plot(vals)
            plt.ylabel('some numbers')
            plt.show()  # TODO: Plot should not be continuous (dots not lines)

    def ShowResultDiff(self, threshold):
        with self.m_lock:
            if self.m_state is not State.done:
                raise Exception("Invalid in this state")

            resultFrames = self.getResultFrames_()

            for i in range(len(resultFrames)):
                if i != self.m_resultIndexes[0]:
                    diff = cv2.absdiff(resultFrames[i], resultFrames[i - 1])  # Duplicate from Diff_
                    ret, diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

                    cv2.imshow('frame', diff)

                    if cv2.waitKey(0) & 0xFF == ord('q'):
                        break

        cv2.destroyAllWindows()

    def Calculate_(self, groupSize, lookback, idx):
        hist = []
        histFrames = []
        diff = 0

        # Once buffer is thread/process safe, and calculation is parallelized, the buffer should be shared by all processes
        consumer = FrameBuffer(self.m_path, groupSize).getConsumer()

        while True:
            assert idx >= len(hist) * groupSize

            hist.append(idx)
            histFrames.append(consumer.getFrame(idx)) # TODO: Should not be storing all. Delete old ones

            startIdx = len(hist) * groupSize

            if startIdx + groupSize - 1 >= self.m_numFrames:  # TODO: Consider ways of handling remainder frames
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
                    idiff += self.Diff_(consumer.getFrame(iidx), histFrames[back])

                if minDiff is None or idiff < minDiff:
                    minDiffIdx = iidx
                    minDiff = idiff

            diff += minDiff
            idx = minDiffIdx

            # For multiprocessing, progress will need to be stored in a shared memory map using "Value". It has a built in lock fyi
            with self.m_lock:
                self.m_progress += 100 / self.m_numFrames

    def Read_(self):
        cap = cv2.VideoCapture(self.m_path)

        self.m_frameRate = cap.get(cv2.CAP_PROP_FPS)
        self.m_numFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        cap.release()

    def Diff_(self, A, B):
        diff = cv2.absdiff(A, B)
        ret, thresh = cv2.threshold(diff, self.mk_threshold, 1, cv2.THRESH_BINARY)
        sum = cv2.sumElems(thresh)[0]
        return sum

    def getResultFrames_(self):
        resultFrames = []
        consumer = FrameBuffer(self.m_path, 0).getConsumer()
        for f in self.m_resultIndexes:
            resultFrames.append(consumer.getFrame(f))

        return resultFrames
