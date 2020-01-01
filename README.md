# SmoothLapse
Smooth 3D printer timelapses without any g-code modification. By selecting similar frames from a higher fps video, SmoothLapse outputs a faster and smoother timelapse. 

## Demos

[![SmoothLapse Demo #1: Smooth 3d printed timelapses](https://i.imgur.com/2IVodfx.png)](https://www.youtube.com/watch?v=7PBDSTGyKH0)

[![SmoothLapse Demo #2: Smooth 3d printed timelapses](https://imgur.com/SCa3PiG.png)](https://www.youtube.com/watch?v=v2vSaOxXVXg)

## Notes
* The algorithm works by splitting the frames into "frame groups", for each frame group we pick the frame that most closely matches the last few frames ("lookback"). We do this for all possible initial frames. The number of possible initial frames is equal to the "group size". "Group size" is also effectively the factor by which the video is sped up. 
* I've personally found that 2*(total frames)/(total layers) is a good group size. Although this is likely not the optimum and your results may vary. It's best to try different values for yourself. Lookback of 5 has proven to be a good balance of performance and quality.
* At this stage, SmoothLapse is still a work in progress and proof of concept.
* Lots of experimentation is still required to develop a faster and better performing algorithm.
* Smoothlapse is currently quite slow. Profiling it proves that most of the time is spent comparing frames and loading the video. Although I've been focusing on optimizing single-thread performance, the code is written to make multiprocessing easy to implement. It is the logical next step, and will greatly improve the computation speed.

## Requirements
* Python 3.7

## How to
### Windows CLI
```
git clone https://github.com/SilentSys/SmoothLapse.git SmoothLapse
cd SmoothLapse
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python smoothlapse.py input.mpg output.mp4 10 10
```

### Ubuntu 19.10 CLI
```
git clone https://github.com/SilentSys/SmoothLapse.git SmoothLapse
cd SmoothLapse
python3 -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
python smoothlapse.py input.mpg output.mp4 10 10
```