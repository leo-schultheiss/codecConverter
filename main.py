import os
import sys

import ffmpeg

converted_tag = '_CONVERTED'
use_cuda = False
video_br = 25
audio_br = 320
supported_video_codecs = ['h264', 'av1']
supported_audio_codecs = ['aac', 'eac3', 'flac']


def get_video_files(path: str):
	video_formats = ['.mp4', '.mkv']
	files = []
	for root, _, fs in os.walk(path):
		for file in fs:
			if not file.__contains__(converted_tag) and video_formats.__contains__(get_extension(file)):
				files.append(os.path.join(root, file))
	files.sort()
	return files


def get_extension(path: str):
	split = path.split('.')
	return '.' + split[len(split) - 1]


def get_codecs(path: str) -> [str, str]:
	streams = ffmpeg.probe(path)["streams"]
	if len(streams) < 2:
		print('file does not appear to contain an audio stream: ' + path)
	video_stream = streams[0]
	audio_stream = streams[1]
	a_codec = audio_stream['codec_name']
	v_codec = video_stream['codec_name']
	return [a_codec, v_codec]


def convert_codecs(path: str, a_codec: str, v_codec: str):
	out_path = path.replace(get_extension(path), converted_tag + get_extension(path))
	command = 'ffmpeg '
	if use_cuda:
		command += '-hwaccel cuda -hwaccel_output_format cuda '
	# -y: override -map 0: select all streams -c:s copy subtitles -c:a select audio codec
	command += '-stats -i \"' + path + '\" -y -map 0 -c:s copy -c:a '
	# audio codec
	if not supported_audio_codecs.__contains__(a_codec):
		# convert to aac with fixed bitrate
		command += 'aac -ab %iK  ' % audio_br
	else:
		command += 'copy '
	# video codec
	command += '-c:v '
	if not supported_video_codecs.__contains__(v_codec):
		if use_cuda:
			# h264_nvenc: cuda encoder -cq:v video bitrate -vf: convert to 8 bit
			command += 'h264_nvenc -cq:v %i -vf scale_cuda=format=yuv420p ' % video_br
		else:
			# encode to h264 encoder -crf: bitrate -vf: convert to 8 bit
			command += 'libx264 -crf %i -vf format=yuv420p ' % video_br
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
	for c, _, _ in in_fs:
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


def get_parameters():
	global use_cuda, video_br, audio_br
	inp = input('cuda hw accel, y/N, default %s:' % str(use_cuda))
	use_cuda = inp.lower() == 'y'
	inp = input('video bitrate, integer 0(lossless)-51(max compression), default %i: ' % video_br)
	if inp.lower().isnumeric():
		video_br = int(inp)
	inp = input('audio bitrate, integer, default %ikb/s: ' % audio_br)
	if inp.lower().isnumeric():
		audio_br = int(inp)


def search_unconverted_videos():
	global f, audio_codec, video_codec
	for f in paths:
		audio_codec, video_codec = get_codecs(f)
		if not supported_video_codecs.__contains__(video_codec) or not supported_audio_codecs.__contains__(audio_codec):
			print(f + ' will be converted: video codec ' + video_codec + " audio codec " + audio_codec)
			input_files.append([f, audio_codec, video_codec])


if __name__ == "__main__":
	p = input("folder to convert codecs in: ")
	paths = get_video_files(p)
	if len(paths) == 0:
		print("no video files detected")
		exit(0)
	input_files = []
	output_files = []
	# filter out files with
	search_unconverted_videos()
	if len(input_files) == 0 or input('start converting? [y/n]').lower() != 'y':
		print("no files to be converted")
		exit(0)
	# get parameters from user
	get_parameters()
	for f, audio_codec, video_codec in input_files:
		print('converting codecs on ' + f)
		output = convert_codecs(f, audio_codec, video_codec)
		output_files.append(output)
	print_file_size_delta(output_files)
	if len(output_files) > 0 and input('remove %i files and rename new files? [y/N]: ' % len(input_files)) == 'y':
		remove_source_files(input_files)
		remove_converted_tags(output_files)
