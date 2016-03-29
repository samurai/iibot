#!/usr/bin/python2.7

import iibotng
import random

def helpMe(self, datestamp, user, message, key):
	self.writeResource(self.iidir + "/" + key + "/in", "No help available, %s" %( user ))

def sayHello(self, datestamp, user, message, key):
	his = ['hello','hi','sup','yo']
	self.writeResource(key + "/in", his[random.randint(0,3)] + ", " + user)

def doTest(self, datestamp, user, message, key):
	self.writeResource(key + "/in","test...")



ayeye = iibotng.iibot("AyEye","/var/iidir/")
ayeye.connect("irc.freenode.org",1)
ayeye.joinChannel("irc.freenode.org", "#rawptest")
ayeye.connect("irc.psych0tik.net",1)
ayeye.joinChannel("irc.psych0tik.net","#t3hpub")
ayeye.addCommand("help",helpMe)
ayeye.addWatchPhrase(["hello","hi","sup"],sayHello)
ayeye.addWatchPhrase("test",doTest)

while not ayeye.halt:
	messages = ayeye.getMessages()
	if messages:
		print messages
