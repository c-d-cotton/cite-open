" VIM_PREAMBLE_START_STANDARD:{{{
" Christopher Cotton (c)
" http://www.cdcotton.com

func! GetProjectDir(curfile)
    if a:curfile[0] == '/'
        let slashtype = '/'
    else
        let slashtype = '\'
    endif

    :let curfilesplit = split(a:curfile, slashtype)

    :while 1
        if slashtype == '/'
            :let prodir =  slashtype . join(curfilesplit, slashtype) . slashtype
        else
            :let prodir =  join(curfilesplit, slashtype) . slashtype
        endif
        
        :if isdirectory(prodir)
            :if isdirectory(prodir . ".git")
                :return(prodir)
            :endif
        :endif

        :if len(curfilesplit) == 1
            :break
        :endif
        :let curfilesplit = curfilesplit[0:-2]

    :endwhile
endfunc

:let s:curfile = expand("<sfile>")
:let s:__projectdir__ = GetProjectDir(s:curfile)

" VIM_PREAMBLE_END:}}}

func! OpenCitation()
    :let l:bytes = line2byte(line(".")) + col(".")
    :let l:fescape = fnameescape(expand("%:p"))
    if !exists("g:externalaltlabelsfileslist")
        let g:externalaltlabelsfileslist = []
    endif
    :let l:strtosend = l:fescape . ' ' . l:bytes . ' --externalaltlabelsfiles ' . join(g:externalaltlabelsfileslist)

    :let l:strtoparse = system(s:__projectdir__ . "run/opencitation.py " . l:strtosend)


endfunc
