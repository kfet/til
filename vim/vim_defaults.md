## My preferred VIM defaults

* pull-in the defaults that most users want
* setup pasting
* tabs, backspace
* line and col numbering.
* search deafults (ignore case, highlight, incremental)
* file type-specific indent, syntax, handling of ION files

----
`cat ~/.vimrc`:

```
" Get the defaults that most users want
source $VIMRUNTIME/defaults.vim

set paste
set expandtab
set tabstop=4
set backspace=indent,eol,start
set ruler
set nu

" search: ignore case, highlight, incrementally
set ignorecase
set hlsearch
set incsearch

if &compatible
  set nocompatible
endif

filetype plugin indent on
syntax enable

au BufRead,BufNewFile *.dp setfiletype ion

```