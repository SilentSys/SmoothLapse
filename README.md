# SmoothLapse
Smooth 3D printer timelapses without any g-code modification

## Demos

[![SmoothLapse Demo #1: Smooth 3d printed timelapses](https://i.imgur.com/2IVodfx.png)](https://www.youtube.com/watch?v=7PBDSTGyKH0)

[![SmoothLapse Demo #2: Smooth 3d printed timelapses](https://imgur.com/SCa3PiG.png)](https://www.youtube.com/watch?v=v2vSaOxXVXg)

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

### Ubuntu CLI (WIP, NEEDS TESTING)
```
git clone https://github.com/SilentSys/SmoothLapse.git SmoothLapse
cd SmoothLapse
python3 -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
python smoothlapse.py input.mpg output.mp4 10 10
```