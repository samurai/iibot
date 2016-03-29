#!/bin/bash

source iibot.cfg

/usr/bin/ii -s $HOST -n $BOTNAME -i $IIDIR &
sleep 3
#cd $IIDIR/$HOST/
echo "/j #rawptest" > $IIDIR/$HOST/in



