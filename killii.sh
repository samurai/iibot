#!/bin/bash

ps aux | grep ii | awk '{print $2}' | xargs kill -9