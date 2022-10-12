import os
import sys

import ffmpeg

converted_tag = '_CONVERTED'
use_cuda = False
convert_audio = False
video_br = 25
audio_br = 320
supported_video_codecs = ['h264', 'av1']
# todo test eac3, flac
supported_audio_codecs = ['aac', 'eac3', 'flac']


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
	return '.' + split[len(split) - 1]


def getCodecs(path: str) -> [str, str]:
	streams = ffmpeg.probe(path)["streams"]
	video_stream = streams[0]
	audio_stream = streams[1]
	a_codec = audio_stream['codec_name']
	v_codec = video_stream['codec_name']
	return [a_codec, v_codec]


def convertCodecs(path: str, a_codec: str, v_codec: str):
	out_path = path.replace(getExtension(path), converted_tag + getExtension(path))
	command = 'ffmpeg '
	if use_cuda:
		command += '-hwaccel cuda -hwaccel_output_format cuda '
	command += '-stats '
	command += '-i \"' + path + '\" '
	# override
	command += '-y '
	# copy all streams
	command += '-map 0 '
	# copy subtitle streams
	command += '-c:s copy '
	# address audio stream
	command += '-c:a '
	# audio codec
	if not supported_audio_codecs.__contains__(a_codec):
		command += 'aac '
		command += '-ab %iK  ' % audio_br
	else:
		command += 'copy '
	# video codec
	command += '-c:v '
	if not supported_video_codecs.__contains__(v_codec):
		if use_cuda:
			# cuda encoder
			command += 'h264_nvenc '
			# bitrate
			command += '-cq:v %i ' % video_br
			# format
			command += '-vf scale_cuda=format=yuv420p '
		else:
			# ffmpeg native h264 encoder
			command += 'libx264 '
			# bitrate
			command += '-crf %i' % video_br
			# video format or smth
			command += ' -vf format=yuv420p '
	else:
		command += 'copy '
	command += '\"' + out_path + '\"'
	print(command)
	return_code = os.system(command)
	if return_code != 0:
		print('error converting codecs on file ' + path, file=sys.stderr)
		exit(-1)
	return out_path


def print_file_size_delta(out_fs):
	for file in out_fs:
		out_size = os.path.getsize(file)
		in_size = os.path.getsize(file.replace(converted_tag, ''))
		print(file + ' size delta is ' + str((out_size - in_size) / 1000_000) + 'MB')


def remove_source_files(in_fs):
	for c in in_fs:
		print('removing ' + c)
		try:
			os.remove(c)
		except FileNotFoundError:
			print('file already removed')


def remove_converted_tags(out_fs):
	for o in out_fs:
		new_name = o.replace(converted_tag, '')
		print('renaming ' + o + ' to ' + new_name)
		os.rename(o, new_name)


if __name__ == "__main__":
	p = input("folder to convert codecs in:\n")
	paths = getFiles(p)
	inp = input('should audio get converted to aac, if not already in a compatible codec, y/N, default %s:\n' % str(
		convert_audio))
	if inp.lower() == 'y':
		convert_audio = True
	print(convert_audio)
	input_files = []
	output_files = []
	# filter out files with
	for f in paths:
		audio_codec, video_codec = getCodecs(f)
		if not supported_video_codecs.__contains__(video_codec) or \
				(convert_audio and not supported_audio_codecs.__contains__(audio_codec)):
			print(f + ' will be converted: video codec ' + video_codec + " audio codec " + audio_codec)
			input_files.append([f, audio_codec, video_codec])
	if input('start converting? [y/n]').lower() != 'y':
		exit(0)
	# parameters
	inp = input('cuda hw accel, y/N, default %s:' % str(use_cuda))
	use_cuda = inp.lower() == 'y'
	print(use_cuda)
	inp = input('video bitrate, integer 0(lossless)-51(max compression), default %i: ' % video_br)
	if inp.lower() == 'y':
		video_br = int(inp)
	print(video_br)
	inp = input('audio bitrate, integer, default %ikb/s: ' % audio_br)
	if inp.lower() == 'y':
		audio_br = int(inp)
	print(audio_br)
	for f, audio_codec, video_codec in input_files:
		print('converting codecs on ' + f)
		output = convertCodecs(f, audio_codec, video_codec)
		output_files.append(output)
	print_file_size_delta(output_files)
	if len(output_files) > 0 and input('remove %i files and rename new files? [y/N]: ' % len(input_files)) == 'y':
		remove_source_files(input_files)
		remove_converted_tags(output_files)
