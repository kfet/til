# Use FFMPEG to cut and concatenate MP4 files

Cut out a portion of a video (starting at 40m 14s, 2m duration) and save it in another file:
```
ffmpeg -i input_video.mp4 -ss 00:10:14 -t 00:02:00 output_video.mp4
```

Concatenate several input MP4 files into one (from [SO](https://stackoverflow.com/questions/7333232/how-to-concatenate-two-mp4-files-using-ffmpeg)):
```
$ cat mylist.txt
file '/path/to/file1'
file '/path/to/file2'
file '/path/to/file3'

$ ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4
```
