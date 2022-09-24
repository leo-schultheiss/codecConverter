import os
import sys
import ffmpeg

converted_tag = '_CONVERTED'


def getFiles(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for file in fs:
			files.append(os.path.join(root, file))
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
	command = 'ffmpeg -y -i \"' + path + '\" -map 0 '
	if a_codec != 'aac':
		command += '-c:a aac -ab 320K '
	else:
		command += '-c:a copy '
	if v_codec != 'h264':
		command += '-c:v libx264 -crf 23 -vf format=yuv420p '
	else:
		command += '-c:v copy '
	command += '\"' + out_path + '\"'
	print(command)
	return_code = os.system(command)
	if return_code != 0:
		print('error converting codecs on file ' + path, file=sys.stderr)
		exit(-1)
	return out_path


if __name__ == "__main__":
	p = input("folder to convert codecs in:\n")
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
