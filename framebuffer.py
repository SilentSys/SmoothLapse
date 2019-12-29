import cv2

class BufferConsumer:
    currentFrameIdx = 0
    frameBuffer = None

    def __init__(self, frameBuffer):
        self.frameBuffer = frameBuffer

    def getFrame(self, frameIdx):
        self.currentFrameIdx = frameIdx

        return self.frameBuffer.getFrame_(frameIdx)

    def release(self):
        self.frameBuffer.consumerList.remove(self)
        self.frameBuffer = None
        self.currentFrameIdx = None

class FrameBuffer:  # TODO: Currently not thread/process safe and does not buffer future groups
    path_ = None
    minBufferSize_ = None
    numHistory_ = None
    frameIdx_ = 0
    frames_ = []
    maxNumFrames_ = None

    cap_ = None

    consumerList = []

    def __init__(self, path, numHistory, minBufferSize=1000):
        if minBufferSize < 0 or numHistory < 0:
            raise Exception("Invalid arguments")

        self.path_ = path
        self.numHistory_ = numHistory
        self.minBufferSize_ = minBufferSize
        self.cap_ = cv2.VideoCapture(path)
        self.maxNumFrames_ = int(self.cap_.get(cv2.CAP_PROP_FRAME_COUNT))

    def __del__(self):
        self.cap_.release()

    def getConsumer(self):
        consumer = BufferConsumer(self)
        self.consumerList.append(consumer)
        return consumer

    def pruneBuffer_(self):
        minFrame = 0
        for c in self.consumerList:
            consumerFrame = c.currentFrameIdx
            if not minFrame or consumerFrame < minFrame:
                minFrame = consumerFrame

        assert minFrame >= self.frameIdx_

        if minFrame - self.numHistory_ > self.frameIdx_:
            for _ in range(minFrame - self.numHistory_ - self.frameIdx_):
                del self.frames_[0]
                self.frameIdx_ += 1


    def getFrame_(self, frameIdx):  # frame idx is the idx inside of group
        if frameIdx < self.frameIdx_:
            raise Exception("Cannot get frame from past")

        self.loadFrames_(frameIdx)

        return self.frames_[frameIdx - self.frameIdx_] #throws if no more frames in file

    def loadFrames_(self, frameIdx): # TODO: Put in own process. Let others wait for new frames
        if frameIdx < self.frameIdx_:
            raise Exception("Cannot load past frame")
        elif frameIdx + self.minBufferSize_ < self.frameIdx_ + len(self.frames_) - 1:
            return

        framesNeeded = min(frameIdx + self.minBufferSize_ - (self.frameIdx_ + len(self.frames_) - 1),
                           self.maxNumFrames_-1 - (self.frameIdx_ + len(self.frames_) - 1))


        if framesNeeded is 0:
            return

        newFrames = []
        for _ in range(framesNeeded): # unlock for just this loop, but must prevent others from starting to load
            ret, frame = self.cap_.read()

            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.resize(frame, (100, 100))
            newFrames.append(frame)

        self.frames_ = self.frames_ + newFrames

        self.pruneBuffer_()
