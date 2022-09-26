import os
import sys
import ffmpeg

converted_tag = '_CONVERTED'
video_br = 23
audio_br = 320


def getFiles(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for file in fs:
			if not file.__contains__(converted_tag):
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
		# h264 encoder
		command += 'libx264 '
		# bitrate
		command += '-crf %i' % video_br
		# codec format or smth
		command += ' -vf format=yuv420p '
		# less deblocking or smth
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
	br = input('video bitrate , integer (0(lossless)-51(max compression), %i default: ' % video_br)
	if br != '':
		video_br = int(br)
	br = input('audio bitrate, integer, %ikb/s default: ' % audio_br)
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
	converted_num = len(converted_files)
	if converted_num > 0 and (input('remove %i files and rename new files? [y/N]: ' % converted_num) == 'y'):
		for c in converted_files:
			print('removing ' + c)
			try:
				os.remove(c)
			except FileNotFoundError:
				print('file already removed')
		for o in output_files:
			new_name = o.replace(converted_tag, '')
			print('renaming ' + o + ' to ' + new_name)
			os.rename(o, new_name)
