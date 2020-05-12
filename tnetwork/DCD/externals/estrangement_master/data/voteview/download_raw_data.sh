#!/bin/bash

#raw senate roll call data gotten via the following bash cmds

mkdir senate_rollcall_raw
cd senate_rollcall_raw
for i in `seq 10 111`; do (wget ftp://voteview.com/dtaord/sen${i}kh.ord) ; done
for i in `seq 1 9`; do (wget ftp://voteview.com/dtaord/sen0${i}kh.ord) ; done

#raw house roll call data gotten via the following bash cmds

#for i in `seq 10 111`; do wget ftp://voteview.com/dtaord/hou${i}kh.ord ; done
#for i in `seq 1 9`; do wget ftp://voteview.com/dtaord/hou0${i}kh.ord ; done

