#!/usr/bin/python
##iibot framework - samurai 
##version 3.0 - 09/25/2010

##IMPORTS## ... obviously?
import time
from random import randint

##BOT FUNCTIONS##
def sendMessage(resource, message):
	if message[-1] != "\n":
		message = message + "\n"
	resource.write(message)
	resource.flush()
	return 0

def voice(nick, channel):
	if users[nick]['voice'] != 1:
		sendMessage(chanserv, "voice %s %s" %(channel, nick))
		users[nick]['voice'] = 1	
		sendMessage(logger, "%s has been given voice" % (nick))

def kick(nick, channel,  message):
	if nick != state['mynick']:
		sendMessage(chanserv, "KICK %s %s %s" % ( channel, nick, message))
		sendMessage(logger, "%s was kicked from the channel - %s" % ( nick, message))
		delUser(nick, users)

def addUser(nick, users):
	if nick in users.keys():
		return users
	else:
		users[nick] = {'message_times':[], 'joined':time.time(), 'voice':0}
		if nick != state['mynick']:
			sendMessage(output, "Welcome to the room, %s" % (nick))
			##need to do this to initialize the PM FIFO's, there's a patch to auto-do this, but I'm not using it currently
			sendMessage(output, "/j %s Welcome to %s, %s" % (nick, state['mychannel'],  nick)) 
			open("../"+nick.lower()+"/out","w").close() ## clear this
			sendMessage(logger, "%s has joined the room" % (nick))
		return users

def delUser(nick, users):
	del(users[nick])
	sendMessage(logger, "%s has left the room" % (nick))
	return users


def resetUsers(users):
	newusers = {}
	for nick in users:
		newusers = addUser(nick, newusers)
	return newusers


##COMMAND FUNCTIONS## below here!
#print out the user object (mostly for debugging)
def stats(args, nick):
	if not nick in users.keys():
		return ""
	result = "/j %s " % (nick)
	for key in users[nick].keys():
		result = result + key + ":" + str(users[nick][key]) + ","
	return result + "\n"

#return to the user, in a PM, the "help menu" 
def help(args, nick):
	for cmd in COMMANDS.keys():
		helpmsg = "" ##later this may support an info message
		sendMessage(output,"/j %s !%s %s" % (nick, cmd, helpmsg))


##INITIALIZATIONS##
#connections
open("out","w").close() ## clear the file, to avoid issues when restarting the bot
input = open("out","r") ## ii is looking at these files from it's perspective, let's swap that so we dont confuse ourselves
output = open("in","a") ## see above
chanserv = open("../chanserv/in","a") ##handle to chanserv, so that we can do MODE changes
logger = open("./logs","a") ## log, you can also point this at one of ii's FIFO's :D

#state - so the bot knows what's up
state = {}
state['mynick'] = 'iibot' ##bot's nickname
state['mychannel'] = '#testingit' ##channel this bot is in (currently only supports 1 channel + PMs)
state['flood_max'] = 15.0 #sending more than 10 messages in 15 seconds? that's a kick for you! 

#users object
users = addUser(state['mynick'],{}) ## init this and add the bot

#command config
COMMAND_CHAR = "!" ##commands will begin with this ,e.g. !help - would return the help menu (in a PM)
COMMANDS = {} ##init
COMMANDS['stats'] = stats ##the key for the array, is the command name, the value is the funciton
COMMANDS['help'] = help   ##e.g. COMMANDS['cmd'] = help, would make !cmd return the help menu

##RUNTIME##
lines = ['']
while 1:
	line = lines.pop()  ##get the message we want to respond to, this is processed below
	if '' in lines: ##clear any null messages
		lines.remove('') 
	lines.append(input.readline().replace("\n","")) ##get a new message and push it onto our input list
	if line != "": ##if the line actually has data (pythonw will return "" when readline fails)
		message_time = line[:17] ##get the time ii reports
		nick = line[17:].split(" ")[0].replace("<","").replace(">","") ##nick (sometimes this is part of a join/part message and not the actual nick... yet)
		message = " ".join(line[17:].split(" ")[1:]) ## grab the message
		##flood control
		if nick in users.keys(): ##if we've already added this user
			if len(users[nick]['message_times']) >= 10: ## this keeps a list of the 10 last message times, for flood kicking and such
				users[nick]['message_times'] = users[nick]['message_times'][1:]
				users[nick]['message_times'].append(time.time())
				if users[nick]['message_times'][9] - users[nick]['message_times'][0] < state['flood_max']: ##here's that kick I promised
					kick(nick, state['mychannel'], "No Flooding!")
			else: 
				users[nick]['message_times'].append(time.time())  
		##users entering or leaving
		if nick == "-!-":
			tmp = message.split("(")
			nick = tmp[0]
			if "has joined" in message:
				users = addUser(nick, users)
			if "has left" in message and nick in users.keys():
				users = delUser(nick, users)
		##any other message
		else: ##we pretty much addUser() regardless, as the function itself does checks for already existing users
			users = addUser(nick, users)
	
		##we've got a command
		if message[0] == COMMAND_CHAR and nick != state['mynick']: ##command processing
			tmp = message[1:].split(" ") ##parsing out the command/args
			command = tmp[0].lower()
			args = " ".join(tmp[1:])
			if command in COMMANDS.keys(): ##if this command is allowed
				result = COMMANDS[command](args, nick) ##run and return
				if result != None and result != "":
					sendMessage(output, result)
			else: ##when we dont know the command
				sendMessage(output, "Eh?\n") 
	else: ##when no message comes through, aka non-response code
		for nick in users.keys(): ##check the bot's PMs
			if nick != state['mynick']: 
				pm = open("../"+nick.lower()+"/out","r") ##remember we cleared this when we add the user
				for i in pm.read().split("\n"):
					if i != "": ##we dont need to add null lines
						lines.append(i) ##add the line to our input processing list
				pm.close() ##close this handle
				open("../"+nick.lower()+"/out","w").close() ##clean up 
