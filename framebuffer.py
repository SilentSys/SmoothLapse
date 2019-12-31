import cv2


class BufferConsumer:

    def __init__(self, frameBuffer):
        self.currentFrameIdx = 0
        self.frameBuffer = frameBuffer

    def getFrame(self, frameIdx):
        self.currentFrameIdx = frameIdx

        return self.frameBuffer.getFrame_(frameIdx)

    def release(self):
        if not self.frameBuffer:
            return

        self.frameBuffer.consumerList_.remove(self)
        self.frameBuffer = None
        self.currentFrameIdx = None


class FrameBuffer:  # TODO: Currently not thread/process. Buffer kinda sucks too (not threaded/process)

    def __init__(self, path, numHistory, minBufferSize=100, frameMap=None):
        if minBufferSize < 0 or numHistory < 0:
            raise Exception("Invalid arguments")

        self.path_ = path
        self.numHistory_ = numHistory
        self.minBufferSize_ = minBufferSize
        self.cap_ = cv2.VideoCapture(path) # TODO: Apparently this can be used for webstreams too. Block on new frames and we can calculate real-time
        self.maxNumFrames_ = int(self.cap_.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frameRate_ = self.cap_.get(cv2.CAP_PROP_FPS)
        self.frameMap_ = frameMap
        self.frameIdx_ = 0
        self.frames_ = []

        self.consumerList_ = []

    def __del__(self):
        self.cap_.release()

    def getFrameCount(self):
        if self.frameMap_:
            return len(self.frameMap_)
        else:
            return self.maxNumFrames_

    def getFrameRate(self):
        return self.frameRate_

    def getConsumer(self):
        consumer = BufferConsumer(self)
        self.consumerList_.append(consumer)
        return consumer

    def pruneBuffer_(self):
        if not self.consumerList_:
            return

        minFrame = 0
        for c in self.consumerList_:
            consumerFrame = c.currentFrameIdx
            if not minFrame or consumerFrame < minFrame:
                minFrame = consumerFrame

        assert minFrame >= self.frameIdx_

        if minFrame - self.numHistory_ > self.frameIdx_:  # TODO: Account for framemap
            for _ in range(minFrame - self.numHistory_ - self.frameIdx_):
                del self.frames_[0]
                self.frameIdx_ += 1

    def getFrame_(self, frameIdx):  # frame idx is the idx inside of group
        if frameIdx < self.frameIdx_:
            raise Exception("Cannot get frame from past")

        self.loadFrames_(frameIdx)

        return self.frames_[frameIdx - self.frameIdx_]  # throws if no more frames in file

    def loadFrames_(self, frameIdx):  # TODO: Put in own process. Let others wait for new frames
        if frameIdx < self.frameIdx_:
            raise Exception("Cannot load past frame")
        elif frameIdx + self.minBufferSize_ < self.frameIdx_ + len(self.frames_) - 1:
            return

        startIdx = self.frameIdx_ + len(self.frames_) - 1
        framesNeeded = min(frameIdx + self.minBufferSize_ - startIdx,
                           self.maxNumFrames_ - 1 - startIdx)

        if framesNeeded is 0:
            return

        newFrames = []
        i = 0
        while len(newFrames) < framesNeeded:  # unlock for just this loop, but must prevent others from starting to load
            ret = self.cap_.grab()  # doesnt decode

            if not ret:
                break

            if not self.frameMap_ or i + startIdx in self.frameMap_:
                ret, frame = self.cap_.retrieve()  # decodes

                if not ret:
                    break

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.resize(frame, (100, 100))
                newFrames.append(frame)

            i +=1

        self.frames_ = self.frames_ + newFrames

        self.pruneBuffer_()
