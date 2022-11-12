### Usage
```
codecConverter [-h] [-c CUDA] [-v 0-51] [-a AUDIO_BR] [-f] folder
```
Converts video files in a given folder to more compatible codecs

positional arguments:
  folder
```
options:
  -h, --help            show this help message and exit
  -c CUDA, --cuda CUDA  use nvidia hardware acceleration. Requires cuda to be
                        installed. Default: False
  -v 0-51, --video-br 0-51
                        video bitrate, integer 0 (lossless) -51 (max
                        compression). Default: 21
  -a AUDIO_BR, --audio-br AUDIO_BR
                        audio bitrate. Default: 320kb/s:
  -f, -y, --force       Disable interaction
```