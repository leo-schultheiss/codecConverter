import os

import ffmpeg


def getFiles(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for file in fs:
			files.append(os.path.join(root, file))
	return files


def getExtension(path: str):
	split = path.split('.')
	return split[len(split) - 1]


def getCodec(path: str):
	streams = ffmpeg.probe(path)["streams"]
	video_stream = streams[0]
	codec_name = video_stream['codec_name']
	return codec_name


def convertH265ToH264(path: str):
	pass


if __name__ == "__main__":
	p = input("path to convert hvec/h265 to h264\n")
	paths = getFiles(p)
	for f in paths:
		if getExtension(f) != 'mp4':
			continue
		codec = getCodec(f)

