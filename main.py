import os
import sys
import ffmpeg

converted_tag = '_CONVERTED'
video_br = 18
audio_br = 320


def getFiles(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for file in fs:
			files.append(os.path.join(root, file))
	files.sort()
	return files


def getExtension(path: str):
	split = path.split('.')
	return split[len(split) - 1]


def getCodecs(path: str) -> [str, str]:
	streams = ffmpeg.probe(path)["streams"]
	video_stream = streams[0]
	audio_stream = streams[1]
	a_codec = audio_stream['codec_name']
	v_codec = video_stream['codec_name']
	return [a_codec, v_codec]


def convertCodecs(path: str, a_codec: str, v_codec: str):
	out_path = path.replace('.mp4', converted_tag + '.mp4')
	command = 'ffmpeg -i \"' + path + '\" '
	# override
	command += '-y '
	# copy all streams
	command += '-map 0 '
	# copy subtitle streams
	command += '-c:s copy '
	# address audio stream
	command += '-c:a '
	# audio codec
	if a_codec != 'aac':
		command += 'aac '
		command += '-ab %iK  ' % audio_br
	else:
		command += 'copy '
	# video codec
	command += '-c:v '
	if v_codec != 'h264':
		command += 'libx264 '
		command += '-crf %i' % video_br
		command += ' -vf format=yuv420p '
		command += '-tune film '
	else:
		command += 'copy '
	command += '\"' + out_path + '\"'
	print(command)
	return_code = os.system(command)
	if return_code != 0:
		print('error converting codecs on file ' + path, file=sys.stderr)
		exit(-1)
	return out_path


if __name__ == "__main__":
	# input
	p = input("folder to convert codecs in:\n")
	br = input('video bitrate , integer (0(lossless)-51(max compression), 18 default: ')
	if br != '':
		video_br = int(br)
	br = input('audio bitrate, integer, 320kb/s default: ')
	if br != '':
		audio_br = int(br)

	# main program
	paths = getFiles(p)
	converted_files = []
	output_files = []
	for f in paths:
		audio_codec, video_codec = getCodecs(f)
		# convert codecs if necessary
		if video_codec != 'h264' or audio_codec != 'aac':
			print('converting codecs on ' + f)
			output = convertCodecs(f, audio_codec, video_codec)
			output_files.append(output)
			converted_files.append(f)
	# delete old files and rename new ones
	if input('remove %i files and rename new files? [y/N]: ' % len(converted_files)) == 'y':
		for c in converted_files:
			print('removing ' + c)
			os.remove(c)
		for o in output_files:
			new_name = o.replace(converted_tag, '')
			print('renaming ' + o + ' to ' + new_name)
			os.rename(o, new_name)
