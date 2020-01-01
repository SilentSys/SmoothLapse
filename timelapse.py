import matplotlib.pyplot as plt
import cv2
import threading
from enum import Enum
from framebuffer import FrameBuffer
import detail
from calculator import Calculator


class State(Enum):
    ready = 1
    calculating = 2
    done = 3


class TimeLapse:

    def __init__(self, path, threshold=100):
        self.m_path = path
        self.mk_threshold = threshold
        self.m_resultIndexes = []
        self.m_frameMap = None

        self.m_lock = threading.RLock()
        self.m_progress = 0  # lock required
        self.m_state = State.ready # lock required

    def Smooth(self, groupSize, lookback, blocking=True, numPasses=1):
        with self.m_lock:  # Locking the mutex while calculating would block getProgress
            if self.m_state is State.calculating:
                raise Exception("Invalid in this state")

            if groupSize < 2:
                raise Exception("Invalid groupSize")

            if lookback < 1:
                raise Exception("Invalid lookback")

            self.m_state = State.calculating

        t = threading.Thread(target=self.Smooth_, args=(groupSize, lookback, numPasses))
        t.start()
        if blocking:
            t.join()

    def Smooth_(self, groupSize, lookback, numPasses):# TODO: This can be parallelized. Should use processes, not threads to avoid GIL.
        frameMap = None
        for p in range(numPasses):
            print("Pass %d" % (p+1)) # TODO: Maybe we shouldnt be printing from here
            buffer = FrameBuffer(self.m_path, groupSize, frameMap=frameMap)

            calculators = []
            for i in range(groupSize):
                calculators.append(Calculator(groupSize, lookback, i, buffer, self.mk_threshold))

            numGroups = int(buffer.getFrameCount() / groupSize)

            for _ in range(numGroups):
                for c in calculators:
                    c.Calculate()
                    # For multiprocessing, progress will need to be stored in a shared memory map using "Value". It has a built in lock fyi
                    with self.m_lock:
                        self.m_progress += 100 / (numGroups * groupSize * numPasses)

            minDiff = None
            best = []
            for c in calculators:
                assert c.done
                hist = c.hist
                diff = c.diff
                if minDiff is None or diff < minDiff:  # TODO: Handle two minimums?
                    minDiff = diff  # TODO: "diff" is lookback only. At this point, we can lookforward too. Calc lookforward here to make a better decision?
                    best = hist

            if numPasses > 1:
                if p > 0:
                    best = [frameMap[i] for i in best]

                frameMap = best

        self.m_resultIndexes = best

        with self.m_lock:
            self.m_state = State.done
            self.m_progress = 100

    def getProgress(self):
        with self.m_lock:
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

            cap = cv2.VideoCapture(self.m_path)

            if frameRateOverride:
                frameRate = frameRateOverride
            else:
                frameRate = cap.get(cv2.CAP_PROP_FPS)

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
                    vals.append(detail.Diff(resultFrames[0], resultFrames[1], self.mk_threshold) * 2)

                elif i == len(self.m_resultIndexes) - 1:
                    # last frame
                    vals.append(detail.Diff(resultFrames[len(resultFrames) - 1],
                                           resultFrames[len(resultFrames) - 2], self.mk_threshold) * 2)

                else:
                    vals.append(detail.Diff(resultFrames[i], resultFrames[i + 1], self.mk_threshold) +
                                detail.Diff(resultFrames[i], resultFrames[i - 1], self.mk_threshold))  # should we really go both ways?

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

    def getResultFrames_(self):
        resultFrames = []
        consumer = FrameBuffer(self.m_path, 0).getConsumer()
        for f in self.m_resultIndexes:
            resultFrames.append(consumer.getFrame(f))

        return resultFrames
