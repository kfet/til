## Use Ghostscript to compress PDF files

On macOs
```
brew install ghostcript
```

`dPDFSETTINGS` option values:
* `/prepress` (default) Higher quality output (300 dpi) but bigger size
* `/ebook` Medium quality output (150 dpi) with moderate output file size
* `/screen` Lower quality output (72 dpi) but smallest possible output file size.

```
gs 
 -q -dNOPAUSE -dBATCH -dSAFER \
 -sDEVICE=pdfwrite \
 -dCompatibilityLevel=1.4 \
 -dPDFSETTINGS=/screen \
 -dEmbedAllFonts=true -dSubsetFonts=true \
 -dColorImageDownsampleType=/Bicubic \
 -dColorImageResolution=144 \                `#PDF downsample color image resolution`
 -dGrayImageDownsampleType=/Bicubic \
 -dGrayImageResolution=144 \                 `#PDF downsample gray image resolution`
 -dMonoImageDownsampleType=/Bicubic \
 -dMonoImageResolution=144 \                 `#PDF downsample mono image resolution`
 -sOutputFile=out.pdf \                      `#Output file`
 file.pdf                                    `#Input file`
```
