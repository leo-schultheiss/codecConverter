import os
import sys


def get_mkv_files(p: str):
	tbr = []
	for root, _, fs in os.walk(p):
		for f in fs:
			if f.endswith('.mkv'):
				tbr.append(os.path.join(root, f))
	tbr.sort()
	return tbr


if __name__ == "__main__":
	if len(sys.argv) < 2:
		exit(-1)
	path = sys.argv[1]
	if not os.path.exists(path):
		exit(-1)
	files = get_mkv_files(path)
	for f in files:
		new_name = f.replace('.mkv', '.mp4')
		command = f'ffmpeg -i {f} -map 0 -c copy {new_name}'
		os.system(command)
		print(f"removing {f}")
		os.remove(f)
