import os
import sys

import ffmpeg

converted_tag = '_CONVERTED'
use_cuda = False
video_br = 21
audio_br = 320
supported_video_codecs = ['h264', 'av1']
supported_audio_codecs = ['aac', 'eac3', 'flac']
video_formats = ['.mp4', '.mkv', '.avi']


def get_video_files(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for f in fs:
			if not f.__contains__(converted_tag) and video_formats.__contains__(get_extension(f)):
				files.append(os.path.join(root, f))
	files.sort()
	return files


def get_extension(path: str):
	"""returns: file extension including '.'"""
	split = path.split('.')
	return '.' + split[len(split) - 1]


def get_codecs(path: str) -> [str, str]:
	# todo enable detection of different streams with different codecs (mainly audio)
	streams = ffmpeg.probe(path)["streams"]
	if len(streams) < 2:
		print('file does not appear to contain an audio stream: ' + path, file=sys.stderr)
		exit(0)
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
	for f in out_fs:
		out_size = os.path.getsize(f)
		in_size = os.path.getsize(f.replace(converted_tag, ''))
		print(f + ' size delta is ' + str((out_size - in_size) / 1000_000) + 'MB')


def cleanup(out_fs):
	for f in out_fs:
		new_name = f.replace(converted_tag, '')
		if not os.path.exists(new_name):
			# file has already been renamed/removed
			continue
		print('removing ' + new_name)
		try:
			os.remove(new_name)
		except FileNotFoundError:
			print('file already removed')
		print('renaming ' + f + ' to ' + new_name)
		os.rename(f, new_name)


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


def search_unconverted_videos(in_fs):
	global audio_codec, video_codec
	for f in in_fs:
		audio_codec, video_codec = get_codecs(f)
		if not supported_video_codecs.__contains__(video_codec) or not supported_audio_codecs.__contains__(audio_codec):
			print(f + ' will be converted: video codec ' + video_codec + " audio codec " + audio_codec)
			input_files.append([f, audio_codec, video_codec])


if __name__ == "__main__":
	if len(sys.argv) > 1:
		in_path = sys.argv[1]
	else:
		in_path = input("folder to convert codecs in: ")
	paths = get_video_files(in_path)
	if len(paths) == 0:
		print("no video files detected")
		exit(0)
	input_files = []
	output_files = []
	search_unconverted_videos(paths)
	if len(input_files) == 0 or input('start converting? [y/n]').lower() != 'y':
		print("no files to be converted")
		exit(0)
	# get parameters from user
	get_parameters()
	for file, audio_codec, video_codec in input_files:
		print('converting codecs on ' + file)
		output = convert_codecs(file, audio_codec, video_codec)
		output_files.append(output)
	print_file_size_delta(output_files)
	if len(output_files) > 0 and input('remove %i files and rename new files? [y/N]: ' % len(input_files)) == 'y':
		cleanup(output_files)
