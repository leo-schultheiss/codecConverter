import argparse
import os
import sys

import ffmpeg

converted_tag = '_CONVERTED'
convert_path = ''
cuda_acceleration = False
force_conversion = False
video_br = 21
audio_br = 320
supported_video_codecs = ['h264', 'av1']
supported_audio_codecs = ['aac', 'eac3', 'flac']
video_formats = ['.mp4', '.mkv', '.avi']


def parse_arguments():
	global convert_path, cuda_acceleration, audio_br, video_br, force_conversion
	parser = argparse.ArgumentParser(
		prog='codecConverter',
		description='Converts video files in a given folder to more compatible codecs', )
	parser.add_argument('folder')
	parser.add_argument("-c", "--cuda", type=bool,
						help=f"use nvidia hardware acceleration. Requires cuda to be installed. Default: {cuda_acceleration}")
	parser.add_argument("-v", "--video-br", type=int, choices=range(0, 52), metavar="0-51",
						help=f"video bitrate, integer 0 (lossless) -51 (max compression). Default: {video_br}")
	parser.add_argument("-a", "--audio-br", type=int, help=f"audio bitrate. Default: {audio_br}kb/s:")
	parser.add_argument("-f", '-y', "--force", action='store_true', help="Disable interaction")
	args = parser.parse_args()
	convert_path = args.folder
	if args.cuda:
		cuda_acceleration = args.cuda
		print(f"Nvidia hardware acceleration set to {cuda_acceleration}")
	if args.video_br:
		video_br = args.video_br
		print(f"video bitrate set to {video_br}")
	if args.audio_br:
		audio_br = args.audio_br
		print(f"audio bitrate set to {audio_br}kb/s")
	force_conversion = args.force


def get_extension(path: str):
	"""returns: file extension including '.'"""
	split = path.split('.')
	return '.' + split[len(split) - 1]


def get_video_files(path: str):
	files = []
	for root, _, fs in os.walk(path):
		for f in fs:
			if not f.__contains__(converted_tag) and video_formats.__contains__(get_extension(f)):
				files.append(os.path.join(root, f))
	files.sort()
	return files


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


def search_unconverted_videos(in_paths) -> [[str, str, str]]:
	global audio_codec, video_codec
	filtered_list = []
	for p in in_paths:
		audio_codec, video_codec = get_codecs(p)
		if not supported_video_codecs.__contains__(video_codec) or not supported_audio_codecs.__contains__(audio_codec):
			red_start = '\033[91m'
			format_end = '\033[0m'
			video_string = video_codec if supported_video_codecs.__contains__(
				video_codec) else f"{red_start}{video_codec}{format_end}"
			audio_string = audio_codec if supported_audio_codecs.__contains__(
				audio_codec) else f"{red_start}{audio_codec}{format_end}"
			print(f"{p} will be converted, video: {video_string} audio: {audio_string}")
			filtered_list.append([p, audio_codec, video_codec])
	return filtered_list


def convert_codecs(path: str, a_codec: str, v_codec: str):
	global cuda_acceleration, video_br, audio_br
	out_path = path.replace(get_extension(path), converted_tag + get_extension(path))
	command = 'ffmpeg '
	if cuda_acceleration:
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
		if cuda_acceleration:
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
		try:
			out_size = os.path.getsize(f)
			in_size = os.path.getsize(f.replace(converted_tag, ''))
			delta = out_size - in_size
			print(f'{f} size delta is {round(delta / 1000_000)}MB | {round(100 * delta / in_size)}%')
		except FileNotFoundError:
			print(f"file not found")


def cleanup(out_fs):
	for f in out_fs:
		new_name = f.replace(converted_tag, '')
		if not os.path.exists(new_name):
			# file has already been renamed/removed
			continue
		print('removing ' + new_name)
		try:
			os.remove(new_name)
			print('renaming ' + f + ' to ' + new_name)
			os.rename(f, new_name)
		except FileNotFoundError:
			print('file already removed')


if __name__ == "__main__":
	parse_arguments()
	paths = get_video_files(convert_path)
	if len(paths) == 0:
		print(f"no video files with extesions {video_formats} detected")
		exit(0)
	input_files = search_unconverted_videos(paths)
	output_files = []
	if len(input_files) == 0:
		print("no files to be converted")
		exit(0)
	if not force_conversion and input('start converting? [y/n]').lower() != 'y':
		exit(0)
	for file, audio_codec, video_codec in input_files:
		print('converting codecs on ' + file)
		output = convert_codecs(file, audio_codec, video_codec)
		output_files.append(output)
	print_file_size_delta(output_files)
	if force_conversion or input(f'remove {len(input_files)} files and rename new files? [y/N]:') == 'y':
		cleanup(output_files)
