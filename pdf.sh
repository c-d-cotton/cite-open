#!/usr/bin/env bash
# BASH_PREAMBLE_START_COPYRIGHT:{{{
# Christopher David Cotton (c)
# http://www.cdcotton.com
# BASH_PREAMBLE_END:}}}

setsid okular "$@" &>'/dev/null' &
