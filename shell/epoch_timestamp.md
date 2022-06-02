## Confert epoch timestamp to human-readable date

To confert 1654189271.097 epoch to a date run this (from [SO](https://unix.stackexchange.com/questions/2987/how-do-i-convert-an-epoch-timestamp-to-a-human-readable-format-on-the-cli)):

Linux:
```
date -d @1654189271.097
```

macOs/BSD:
```
date -r 1654189271
```
