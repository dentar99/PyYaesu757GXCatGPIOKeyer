#!/usr/bin/python3
#
# Author: Tom N4LSJ -- EXPERIMENTAL CODE ONLY FOR TINKERING
#                   -- USE AT YOUR OWN RISK ONLY
#                   -- AUTHOR ASSUMES NO LIABILITY
#
# NO WARRANTY
# NO WARRANTY
# NO WARRANTY
# NO WARRANTY
# NO WARRANTY
#
# Yaesu FT757-GX-1 program by N4LSJ
# 
# This program works for the FT-757GX -MARK 1- only.  The MK2 programming
# is not quite the same, so this program is not considered compatible 
# with the FT-757GX 2.
# 
# SEE OCTOBER 1985 QST ARTICLE PAGE 38 TITLED, "A CAT Control System"
# 
# On page 39, a schematic is there for a circuit that uses a TIL-111
# optoisolator.  You want the TIL-111 optoisolator circuit.  It's the
# cleanest thing I've tried yet.  Other solutions can carry too much
# noise for the overly sensitive TTL level serial interface.
#
# The optoisolator circuit is driven by TTL level, not actual RS-232,
# so you'll want to use TTL level serial, such as from an RS-232 to
# TTL converter.  Don't wire the RS-232 straight to the circuit.
#
# The connector on the back of the YAESU FT-757GX is called a 
# 3-pin JST-XH with 2.54mm pitch
# 
# For keying, a 5V reed relay with a cap across the contacts to
# the rig, and the relay's coil across a GPIO pin and ground, 
# specified in the keyer= variable will work nicely.
# Be sure you know the difference between BOARD and BCM with
# regard to the GPIO library before choosing which pins to tie
# your relay to.
#
# The first time you run this program, it will ask you for your
# Call, a Frequency, WPM, and a serial port.
# 
# If you get something wrong, you can edit or delete your .yaesuft757gx.conf
# file and it will build new next time you run the program
#

# DATA BYTE:
# | START BIT | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | STOP BIT | STOP BIT |

# 5 BYTE BLOCK COMMAND
# | PARM 4 (LSD) | PARM 3 | PARM 2 | PARM 1 | INSTRUCTION (MSD) |

def DEBUG(x):
	global DEBUGTS
	N = datetime.datetime.utcnow()
	print(x + str(N - DEBUGTS))
	DEBUGTS = N 

global DEBUGTS
import datetime
DEBUGTS=datetime.datetime.utcnow()

import time
import serial
import RPi.GPIO as GPIO

from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.simpledialog import askinteger
from tkinter.simpledialog import askfloat
from tkinter.simpledialog import messagebox

from os.path import expanduser
from os import path
from time import sleep

global ee
global sending
global keyer
global ser
global mycall
global geom
global othercall
global rxfreq
global savef
global txfreq
global configfn
global wpm
global cw
global qqsy
global serport

global spinning
global spinning_id
global spinny
global spinspeed

global spinningt
global spinning_idt
global spinnyt
global spinspeedt

global tuning
global tuning_idt

global curspinny
global clock_id
global vfosplit

vfosplit = 0
sending = 0
ee = 0
othercall=''
spinning=0
spinny=['|','/','-','\\']
curspinny=0
tuning=0
tuning_idt=''

################################# YOU SET THESE
### once the config file gets written out, these values
### in that get used instead of what's here
serport='/dev/ttyAMA0'		# PORT TO TALK TO RIG
rxfreq=7.10000			# DEFAULT FREQ TO USE IF NO CONFIG FILE
txfreq=rxfreq			# DEFAULT FREQ TO USE IF NO CONFIG FILE
mycall='CHANGEME'		# EMPTY ON PURPOSE
wpm="13"			# WPM TO USE IF NO CONFIG FILE (FIX THIS)
keyer = 4 #             	# GPIO PIN FOR KEYING TO TRANSISTOR
# IMPORTANT.. Look for setmode below and PAY ATTENTION TO BOARD VS BCM
################################# END OF YOU SET THESE

GPIO.setmode(GPIO.BCM)
GPIO.setup(keyer,GPIO.OUT)

qqsy = [
	("lb","160M"),
	("bb","<F> (EAG)" , "1.8","green"),
	("bb","<F> (EAG)" , "2","green"),
	("sep","x"),
	("lb","80M"),
	("bb","<F> (E)" , "3.5","red"),
	("bb","<F> (EAGnt)" , "3.525","red"),
	("bb","<F> (E)" , "3.6","yellow"),
	("bb","<F> (EA)" , "3.7","green"),
	("bb","<F> (EAG)" , "3.8","green"),
	("bb","<F> (EAG)" , "4","green"),
	("sep","x"),
	("lb","60M"),
	("bb","<F> (EAG)" , "5.332","red"),
	("bb","<F> (EAG)" , "5.348","red"),
	("bb","<F> (EAG)" , "5.3585","red"),
	("bb","<F> (EAG)" , "5.373","red"),
	("bb","<F> (EAG)" , "5.405","red"),
	("sep","x"),
	("lb",""),
	("bb","<F> (EAG)" , "5.3305","green"),
	("bb","<F> (EAG)" , "5.3465","green"),
	("bb","<F> (EAG)" , "5.357","green"),
	("bb","<F> (EAG)" , "5.3715","green"),
	("bb","<F> (EAG)" , "5.4035","green"),
	("sep","x"),
	("lb","40M"),
	("bb","<F> (E)","7","red"),
	("bb","<F> (AGnt)","7.025","red"),
	("bb","<F> (EA)","7.125","yellow"),
	("bb","<F> (EAG)","7.175","green"),
	("bb","<F> (EAG)","7.3","green"),
	("sep","x"),
	("lb","30M"),
	("bb","<F> (EAG)","10.1","red"),
	("bb","<F> (EAG)","10.150","red"),
	("sep","x"),
	("lb","20M"),
	("bb","<F> (E)","14","red"),
	("bb","<F> (EAG)","14.025","red"),
	("bb","<F> (E)","14.15","yellow"),
	("bb","<F> (EA)","14.175","green"),
	("bb","<F> (EAG)","14.225","green"),
	("bb","<F> (EAG)","14.350","green"),
	("sep","x"),
	("lb","17M"),
	("bb","<F> (EAG)","18.068","red"),
	("bb","<F> (EAG)","18.11","yellow"),
	("bb","<F> (EAG)","18.168","green"),
	("sep","x"),
	("lb","15M"),
	("bb","<F> (E)","21","red"),
	("bb","<F> (EAGnt)","21.025","red"),
	("bb","<F> (E)","21.2","yellow"),
	("bb","<F> (EA)","21.225","green"),
	("bb","<F> (EAG)","21.275","green"),
	("bb","<F> (EAG)","21.45","green"),
	("sep","x"),
	("lb","12M"),
	("bb","<F> (EAG)","24.89","red"),
	("bb","<F> (EAG)","24.93","yellow"),
	("bb","<F> (EAG)","24.99","green"),
	("sep","x"),
	("lb","10M"),
	("bb","<F> (EAGNT)","28","red"),
	("bb","<F> (EAGNT)","28.3","yellow"),
	("bb","<F> (EAG)","28.5","green"),
	("bb","<F> (EAG)","29.7","green"),
	("sep","x"),
	("lb","TIME"),
	("dd","W1AW", "1.8175", "3.5815", "7.0475", "14.0475", "18.0975", "21.0675", "28.0675"),
	("dd","WWV", "2.5", "5", "10", "15", "20"),
	("dd","CHU", "7.335", "7.85", "14.67"),
	("sep","x"),
	("lb","VOA"),
	("dd","VOA", "0.909", "1.296", "1.530", "1.575", "4.930", "4.960", "5.925", "5.930", "6.080","6.195","7.270","7.325","7.375","9.815","12.030","13.590","15.460","15.580","15.715","17.530","17.530","17.790"),
]

cw = {
"A" : ".-", "B" : "-...", "C" : "-.-.", "D" : "-..", "E" : ".", "F" : "..-.", 
"G" : "--.", "H" : "....", "I" : "..", "J" : ".---", "K" : "-.-", "L" : ".-..", 
"M" : "--", "N" : "-.", "O" : "---", "P" : ".--.", "Q" : "--.-", "R" : ".-.", 
"S" : "...", "T" : "-", "U" : "..-", "V" : "...-", "W" : ".--", "X" : "-..-", 
"Y" : "-.--", "Z" : "--..", "0" : "-----", "1" : ".----", "2" : "..---", 
"3" : "...--", "4" : "....-", "5" : ".....", "6" : "-....", "7" : "--...", 
"8" : "---..", "9" : "----.", "." : ".-.-.-", "?" : "..--..", "/" : "-..-.",
"," : "--..--", "!" : "-.-.--", "'" : ".----.", "\"" : ".-..-.", "(" : "-.--.",
")" : "-.--.-", "&" : ".-...", ":" : "---...", ";" : "-.-.-.", "_" : "..--.-",
"=" : "-...-", "+" : ".-.-.", "-" : "-....-", "$" : "...-..-", "@" : ".--.-"
}

configfn=str(expanduser("~"))+"/.yaesuft757gx.conf"

##def eventbark(e):
##	print(str(e.widget))

def hovertxt(txt):
	hlabel.config(text=txt)

def hover(widg,txt):
	widg.bind("<Enter>",lambda evt, tt=txt: hovertxt(tt))
	widg.bind("<Leave>",lambda evt, tt="": hovertxt(tt))

def startspinningt(val):
	global vfosplit
	global spinningt
	global spinspeedt
	if (vfosplit == 0):
		return None
	spinspeedt=500
	spinningt = 1
	spinknobt(val)

def pttaction(val):
	if (val == 1):
		ptt_on()
	if (val == 0):
		ptt_off()

def starttuning(val):
	global tuning
	global tuning_idt
	print ("tuning val is "+str(val))
	if (val > 1):
		ptt_on()
		val = val - 1
		tuning_idt=root.after(1000,starttuning,val)
	else:
		root.after_cancel(tuning_idt)
		ptt_off()

#def stoptuning(val):
#	global tuning
#	global tuning_idt
#	root.after_cancel(tuning_idt)
#	ptt_off()


def startspinning(val):
	global spinspeed
	global spinning
	spinspeed=500
	spinning = 1
	spinknob(val)

def stopspinningt(*args):
	global spinningt
	global spinning_idt
	global spinspeedt
	spinningt = 0
	spinspeedt=500
	root.after_cancel(spinning_idt)

def stopspinning(*args):
	global spinning
	global spinning_id
	global spinspeed
	spinning = 0
	spinspeed=500
	spinnything.configure(text="")
	root.after_cancel(spinning_id)

def spinknob(val):
	global curspinny
	global spinny
	global spinning
	global spinning_id
	global spinspeed
	global rxfreq
	curspinny = (curspinny + (1 if val > 0 else -1)) % 4
	spinnything.configure(text=spinny[curspinny])
	rxfreq = round(rxfreq + val,5);
	if (rxfreq > 29.99999):
		rxfreq = .5
	if (rxfreq < .5):
		rxfreq = 29.99999
	FREQ()
	if (spinning == 1):
		spinning_id=root.after(spinspeed,spinknob,val)
		spinspeed = 34 if (spinspeed==67) else spinspeed
		spinspeed = 67 if (spinspeed==125) else spinspeed
		spinspeed = 125 if (spinspeed==250) else spinspeed
		spinspeed = 250 if (spinspeed==500) else spinspeed

def spinknobt(val):
	global spinnyt
	global spinningt
	global spinning_idt
	global spinspeedt
	global txfreq
	txfreq = round(txfreq + val,5);
	if (txfreq > 29.99999):
		txfreq = .5
	if (txfreq < .5):
		txfreq = 29.99999
	itfreq.delete(0,END)
	itfreq.insert(0,str('%7.5f' % (txfreq)))
	
	if (spinningt == 1):
		spinning_idt=root.after(spinspeedt,spinknobt,val)
		spinspeedt = 34 if (spinspeedt==67) else spinspeedt
		spinspeedt = 67 if (spinspeedt==125) else spinspeedt
		spinspeedt = 125 if (spinspeedt==250) else spinspeedt
		spinspeedt = 250 if (spinspeedt==500) else spinspeedt

def startclock(*args):
	global clock_id
	putdate()
	clock_id=root.after(500,startclock,'')

def putdate():
	datelab.config(text=str(datetime.datetime.utcnow())[0:19]+" UTC")

def dummy():
	return True

def alnumslashonly(val):
	for ch in val:
		if (not ch in ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/')):
			return False
	return True

def cwonly(val):
	global cw
	for ch in val:
		ch=ch.upper()
		if (not ch in cw.keys() and ch != " "):
			print ("BAD CHAR: ["+ch+"]")
			return False
	return True

def WriteCfg():
	global serport
	global rxfreq
	global configfn

	fh=open(configfn,'w+')
	fh.write('rxfreq='+str(rxfreq)+"\n")
	fh.write('wpm='+str(iwpm.get())+"\n")
	fh.write('mycall='+imycall.get()+"\n")
	sx=root.geometry().replace('+',' ').split()[1]
	sy=root.geometry().replace('+',' ').split()[2]
	fh.write("geom=+"+sx+"+"+sy+"\n")
	fh.write("serport="+serport+"\n")
	for kid in macroframe.winfo_children():
		fh.write('macro='+str(kid['text'])+"\n")

	print("Saved config to "+configfn)

def SPLU(*args):
	global vfosplit
	global txfreq
	if (vfosplit == int(1)):
		itfreq.delete(0,END)
		txfreq = txfreq + .001
		itfreq.insert(0,str('%7.5f' % (txfreq)))

def SPLD(*args):
	global vfosplit
	global txfreq
	if (vfosplit == int(1)):
		itfreq.delete(0,END)
		txfreq = txfreq - .001
		itfreq.insert(0,str('%7.5f' % (txfreq)))
		

def VSPL(*args):
	global vfosplit
	vfosplit = int(1 - vfosplit)
	if (vfosplit == int(1)):
		itfreq.config(bg='white')
		spld.config(fg='black')	
		splu.config(fg='black')	
		splsd.config(fg='black')	
		splsu.config(fg='black')	
	else:
		itfreq.delete(0,END)
		itfreq.insert(0,ifreq.get())
		itfreq.config(bg='grey')
		spld.config(fg='grey')	
		splu.config(fg='grey')	
		splsd.config(fg='grey')	
		splsu.config(fg='grey')	
		
	

def QUICKQSY(string):
	global rxfreq
	global txfreq
	global vfosplit
	ifreq.delete(0,END)
	ifreq.insert(0,string)
	rxfreq=float(ifreq.get())
	vfosplit = 1
	VSPL()
	QSY()

def MACGRIDNEW():
	mr = 0
	mc = 0
	gs=macroframe.grid_slaves()
	for s in gs:
		gi=s.grid_info()
		gir=gi['row']
		if (mr < gir):
			mr = gir

	for s in gs:
		gi=s.grid_info()
		gir=gi['row']
		gic=gi['column']
		if (gir == mr and mc < gic):
			mc = gic
	print ("max row is "+str(mr)+" and max col is "+str(mc))
	if (mc == 5):
		return mr+1, 1
	else:
		return mr, mc+1

def MACROREGRID():
	macbuts=[]
	gs=macroframe.grid_slaves()

	for r in range (1,100):
		for c in range (1,6):
			for s in gs:
				gi=s.grid_info()
				rr=gi['row']
				cc=gi['column']
				if (r == rr and c == cc):
					macbuts.append(s)
	rr=1
	cc=1
	for m in macbuts:
		m.grid(row=rr, column=cc)
		cc=cc+1
		if (cc > 5):
			cc=1
			rr=rr+1
				
		

	
def MAKEMACBUT(txt,rr,cc):
	bb=Button(macroframe, text=txt)
	bb.grid(row=rr,column=cc)
	hover(bb,"Hit to send "+txt+", or right click to edit.")
	bb.config(command=lambda widg=bb: RUNMACRO(widg))
	bb.bind("<ButtonRelease-3>", lambda ebe, widg=bb: EDITBTN(widg))
	return bb

def NEWMACRO(*args):
	rr,cc=MACGRIDNEW()
	bb=MAKEMACBUT('NEW MACRO',rr,cc)
	EDITBTN(bb)
	if (bb['text'] == 'NEW MACRO' or bb['text'] == ''):
		bb.destroy()

def EDITBTN(widg):
	newval = askstring('New Macro','Enter new macro. <C> is your call.  <I> is other call.',initialvalue=widg['text'])
	if (newval == ''):
		widg.destroy()
		MACROREGRID()
	else:
		widg.config(text=newval)

def RUNMACRO(widg):
	string=widg['text'].upper().replace('<I>',iothercall.get().upper()).replace('<C>',imycall.get().upper())
	tempstr=cwinput.get()
	cwinput.delete(0,END)
	cwinput.insert(0,string)
	QUEUE()
	cwinput.delete(0,END)
	cwinput.insert(0,tempstr)

#def RUNMACRO(string):
#	string=string.replace('<I>',iothercall.get()).replace('<C>',imycall.get())
#	tempstr=cwinput.get()
#	cwinput.delete(0,END)
#	cwinput.insert(0,string)
#	QUEUE()
#	cwinput.delete(0,END)
#	cwinput.insert(0,tempstr)

def ReadCfg():
	global serport
	global keyer
	global geom
	global rxfreq
	global savef
	global configfn
	global wpm
	global mycall
	global ee

	if (not path.exists(configfn)):
		root.iconify()
		mycall=askstring("Call Sign","Please enter your call sign.").upper().strip()
		wpm=askinteger("WPM","Enter a default words per minute for CW.",minvalue=5,maxvalue=50)
		rxfreq=askfloat("Frequency","Enter the frequency to go to the first time you start.",minvalue=.5,maxvalue=29.99999)
		serport=askstring("Serial Port","Serial Port for CAT, e.g. /dev/ttyUSBx").strip()
		
		
		imycall.delete(0,END)
		imycall.insert(0,mycall)
		iwpm.delete(0,END)
		iwpm.insert(0,wpm)
		zz=Button(macroframe,\
			text='SAMPLE MACRO')
		lmb=lambda widg=zz: RUNMACRO(widg)
		zz.config(command=lmb)
		zz.grid(row=0,column=1)
		WriteCfg()
		zz.destroy()
		imycall.delete(0,END)
		iwpm.delete(0,END)

	if (path.exists(configfn)):
		print ("Reading Config file now that it exists...")
		rr = 1
		cc = 1
		fh=open(configfn,'r')
		cfglines = fh.readlines()
		fh.close()
		for cfgline in cfglines:
			items=cfgline.split('=')
			if (items[0] == "rxfreq"):
				rxfreq=float(items[1].strip())
				savef=rxfreq
			if (items[0] == "wpm"):
				wpm=items[1].strip()
			if (items[0] == "mycall"):
				mycall=items[1].strip()
			if (items[0] == "geom"):
				geom=items[1].strip()
			if (items[0] == "serport"):
				serport=items[1].strip()
			if (items[0] == "macro"):
				macrocontents=items[1].strip()
				MAKEMACBUT(macrocontents,rr,cc)
				cc = cc + 1
			if (cc > 5):
				rr = rr + 1
				cc = 1


		return True
	else:
		print ("No config file yet.")
		return None

def Quitter(*args):
	GPIO.cleanup(keyer)
	WriteCfg()
	root.destroy()

def Send(p4,p3,p2,p1,co,vf):
	global ser


	ser.write(bytes([p4,p3,p2,p1,co]))
	ser.flush()

	if (vf == 0):
		time.sleep(.10)

def SIMPLECMD(byt):
	global rxfreq
	bandstops = [ 0, 1.5, 3.5, 7, 10, 14, 18, 21, 24.5, 28, 30 ]
	#
	# RADIO QUIRK:
	# The 160M band IS correct and mimics the radio when band
	# down is pressed. 2.49999 then BAND DOWN on the radio 
	# results in being put in the 10M band.
	#
	# Other quirk:
	# When going up 500k on front panel button:
	# 29.49999 becomes 29.99999
	# 29.50000 becomes 00.50000
	# When going down 500k on front panel button:
	# 00.50000 becomes 29.50000
	# 00.99999 becomes 29.99999
	bands = [
		[ 1.5, 2.49999 ],
		[ 3.5, 3.99999 ],
		[ 7.0, 7.49999 ],
		[ 10.0, 10.49999 ],
		[ 14.0, 14.49999 ],
		[ 18.0, 18.49999 ],
		[ 21.0, 21.49999 ],
		[ 24.5, 24.99999 ],
		[ 28.0, 29.99999 ]
		]

	if (byt == 17 or byt == 18):
		if (byt == 17):
			if (rxfreq >= 29.5):
				rxfreq = round(rxfreq -29,5)
			else:
				rxfreq = round(rxfreq + .5,5)

		if (byt == 18):
			if (rxfreq <= 0.99999):
				rxfreq = round(rxfreq + 29,5)
			else:
				rxfreq = round(rxfreq - .5,5)

		FREQ()

	elif (byt == 7 or byt == 8):
		mhz = int(rxfreq)
		hun = int(int(rxfreq * 10) - (mhz * 10))
		submhz = float(mhz)
		if (hun >= 5):
			submhz = submhz +float(5/10)
		remmhz = rxfreq - submhz
		nn = 0
		jmpband=float(0)
		for xx in bands:
			if (rxfreq < bands[nn][0]):
				print("You're below the "+str(bands[nn])+" band ")
				if (byt == 7):
					jmpband = float(bands[(nn)%9][0]);
				if (byt == 8):
					jmpband = float(bands[(nn - 1)%9][0]);
				break

			if (bands[nn][0] <= rxfreq <= bands[nn][1]):
				print("You're in the "+str(bands[nn])+" band ")
				if (byt == 7):
					jmpband = float(bands[(nn + 1)%9][0]);
				if (byt == 8):
					jmpband = float(bands[(nn - 1)%9][0]);
				break
			else:
				nn = nn + 1

		rxfreq = round(float(jmpband + remmhz),5)
		FREQ()

	elif (byt == 10):
		QSY()
	else:
		Send(0,0,0,0,byt,1)

def RXQSY(*args):
	global txsav
	global rxsav
	global rxfreq
	global txfreq
	global savef
	rxfreq=rxsav
	txfreq=txsav
	#rxfreq=float(ifreq.get())
	#txfreq=float(itfreq.get())
	FREQ()

def TXQSY(*args):
	global txsav
	global rxsav
	global rxfreq
	global txfreq
	global savef
	txsav=txfreq
	rxsav=rxfreq
	txfreq=float(ifreq.get())
	rxfreq=float(itfreq.get())
	FREQ()


def QSY(*args):
	global rxfreq
	rxfreq=float(ifreq.get())
	txfreq=float(itfreq.get())
	FREQ()

def FREQ():
	global rxfreq
	global txfreq
	freq=(str(rxfreq).strip())
	try:
		dec = freq.index('.')
	except:
		freq = freq + '.'

	if (rxfreq >= 10.00000):
		freq = "0" + freq + "00000"
	else:
		freq = "00" + freq + "00000"

	b1=int((freq[0:2]),16)
	b2=int((freq[2]+freq[4]),16)
	b3=int((freq[5:7]),16)
	b4=int((freq[7:9]),16)
	# 12.345.67 becomes hex 67|45|23|01|0B 
	co=int('0B',16)
	Send(b4,b3,b2,b1,10,vfosplit)
	ifreq.delete(0,END)
	ifreq.insert(0,str('%7.5f' % (rxfreq)))
	if (vfosplit == 0):
		itfreq.delete(0,END)
		itfreq.insert(0,str('%7.5f' % (rxfreq)))
		txfreq=float(itfreq.get())

def ptt_on():
	global keyer
	GPIO.output(keyer,1)
	lcw.config(bg='#00ff00')
	root.update()

def ptt_off():
	global keyer
	lcw.config(bg='#005500')
	root.update()
	GPIO.output(keyer,0)

def KEY(ch):
	global cw
	global keyer
	global wpm
	global vfosplit
	global rxfreq
	global txfreq
	global savef
	
	t = (1200.0/float(wpm))/1000.0
	ditlength = t
	dahlength = ditlength * 3
	if (ch == " "):
		if (vfosplit == 1):
			rxfreq=savef
			FREQ()
		True
	else :
		if (vfosplit == 1 and rxfreq != txfreq):
			rxfreq=txfreq
			FREQ()
		for dd in cw[ch]:
			if (dd == "-"):
				ptt_on()
				sleep(dahlength)
				ptt_off()
				sleep(ditlength)
			if (dd == "."):
				ptt_on()
				sleep(ditlength)
				ptt_off()
				sleep(ditlength)
	root.update()
#	if (vfosplit == 1):
#		rxfreq=savef
#		FREQ()
	sleep (dahlength)
	root.update()

def BCLEAR():
	cwinput.delete(0,END)
	QCLEAR()
	
def QCLEAR():
	global sending
	sending = 0
	queue.delete(0,END)
	
def QUEUE(*args):
	if (queue.get() != ""):
		queue.insert(END," ")
	queue.insert(END,cwinput.get().upper())
	cwinput.delete(0,END)

def STOP():
	global sending
	global rxfreq
	global savef
	sending = 0
	lcw.config(bg='#d9d9d9')
	rxfreq=savef
	FREQ()

def STARTSEND():
	global sending
	global txfreq
	global rxfreq
	global savef
	txfreq=float(itfreq.get())
	savef=rxfreq
	QUEUE()
	if (sending == 0):
		sending = 1
		SENDCW()

def SENDCW():
	global sending
	global wpm
	if (sending == 1):
		wpm=iwpm.get()
		qq = queue.get()
		if (qq == ""):
			print ("Nothing in queue")
			sending = 0
			return None
		key = qq[0]
		qq  = qq[1:]
		queue.delete(0,END)
		queue.insert(0,qq)
#		root.update()
		KEY(key)
#		root.update()
		if (queue.get() != ""):
			SENDCW()
		else:
			sending = 0
			lcw.config(bg='#d9d9d9')
			rxfreq=savef
			FREQ()

root=Tk()

butframe=Frame(root,borderwidth=2,relief="groove")
qsyframe=Frame(root,borderwidth=2,relief="groove")
cwframe=Frame(root,borderwidth=2,relief="groove")
keysframe=Frame(root,borderwidth=2,relief="groove")
macroframe=Frame(root,borderwidth=2,relief="groove")
quickqsyframe=Frame(root,borderwidth=2,relief="groove")
helpframe=Frame(root,borderwidth=2,relief="groove")
ifreqframe=Frame(root,borderwidth=2,relief="groove")
dialbutframe=Frame(root,borderwidth=2,relief="groove")

root.bind("<Escape>",Quitter)
root.bind("<Control-w>",Quitter)
root.protocol("WM_DELETE_WINDOW", Quitter)
root.title("Yaesu FT-757GX (MK1)")

macroframe.bind("<ButtonRelease-3>",NEWMACRO)

# CW FRAME WIDGETS
lqueue = Label(cwframe, text="Queue:")
queue = Entry(cwframe, font="Courier", width=84)
lcw = Label(cwframe, text="CW:")
cwinput = Entry(cwframe, font="Courier", width=40, validate="key")
cwinput['validatecommand']=(cwinput.register(cwonly),'%P')
cwinput.bind("<Return>",QUEUE)
cwinput.bind("<KP_Enter>",QUEUE)
lwpm = Label(cwframe,text="wpm:")
iwpm = Entry(cwframe, font = "Courier", width=2)
clr = Button(cwframe,text="clear queue", command=QCLEAR, width=8, fg="white",bg="blue") 
clrb = Button(cwframe,text="clear both", command=BCLEAR, width=8, fg="white",bg="blue") 
qcw = Button(cwframe,text="queue", command=QUEUE, width=8, bg="yellow") 
bcw = Button(cwframe,text="GO", command=STARTSEND, width=8, bg="green") 
scw = Button(cwframe,text="STOP", command=STOP, width=8, bg="red")

#HELP
hlabel=Label(helpframe,text="")

# CALLSIGN FRAME
lmycall = Label(keysframe, text="Your Station's Call:")
imycall = Entry(keysframe, width=13, validate="key", justify="center")
imycall['validatecommand']=(imycall.register(alnumslashonly),'%P')
lothercall = Label(keysframe, text="Other Station's Call:")
iothercall = Entry(keysframe, width=13, validate="key", justify="center")
iothercall['validatecommand']=(iothercall.register(alnumslashonly),'%P')
lnotes = Label(keysframe, text="<C> is replaced with your call.  <I> is replaced with other station's call.")

ifreq = Entry(ifreqframe, font="Helvetica 44 bold", justify="center", width=9)
ifreq.bind("<Return>",QSY)
ifreq.bind("<KP_Enter>",QSY)
itfreq = Entry(ifreqframe, font="Helvetica 14 bold", justify="center", width=9, bg='grey')
itfreq.bind("<Button-1>",TXQSY)
itfreq.bind("<ButtonRelease-1>",RXQSY)
splu = Button(ifreqframe, text="up 1000", justify="center", width=6, command=SPLU, fg='grey')
vspl = Button(ifreqframe, text="Unbind", justify="center", width=6, command=VSPL)
spld = Button(ifreqframe, text="dn 1000", justify="center", width=6, command=SPLD, fg='grey')
splsu = Button(ifreqframe, text=">>", justify="center", width=2, fg='grey')
splsd = Button(ifreqframe, text="<<", justify="center", width=2, fg='grey')
spllb = Label(ifreqframe, text="(tx freq)")

# RADIO BUTTONS 
split = Button(butframe,text="SPLIT", command=lambda: SIMPLECMD(1), width=11) #1
mrvfo = Button(butframe,text="MR/VFO", command=lambda: SIMPLECMD(2), width=11) #2
vtom = Button(butframe,text="V -> M", command=lambda: SIMPLECMD(3), width=11) #3
dlock = Button(dialbutframe,text="D LOCK", command=lambda: SIMPLECMD(4), width=11) #4
vfoab = Button(butframe,text="VFO A/B", command=lambda: SIMPLECMD(5), width=11) #5
mtov = Button(butframe,text="M -> V", command=lambda: SIMPLECMD(6), width=11) #6
bandup = Button(butframe,text="BAND UP", command=lambda: SIMPLECMD(7), width=11) #7
banddn = Button(butframe,text="BAND DN", command=lambda: SIMPLECMD(8), width=11) #8
clar = Button(dialbutframe,text="CLAR", command=lambda: SIMPLECMD(9), width=11) #9
freq = Button(dialbutframe,text="QSY", command=lambda: SIMPLECMD(10), width=11) #10
vmswap = Button(butframe,text="V<>M", command=lambda: SIMPLECMD(11), width=11) #11
datelab = Label (butframe, font="Helvetica 12 bold", text="YYYY-MM-DDDD HH:MM", width=23)
up500k = Button(butframe,text="500k ^", command=lambda: SIMPLECMD(17), width=11) #17 (made up)
dn500k = Button(butframe,text="500k v", command=lambda: SIMPLECMD(18), width=11) #18 (made up)
ptt = Button(dialbutframe,text="PTT", width=11)
tune = Button(dialbutframe,text="TUNE", width=11)

# VFO SPINNERS
u1000 = Button(qsyframe,text=">1000>", width=5)
u500 = Button(qsyframe,text=">500>", width=5)
u100 = Button(qsyframe,text=">100>", width=5)
u10 = Button(qsyframe,text=">10>", width=5)
spinnything = Label (qsyframe,text=" ",font="Helvetica 16 bold", width=3)
d10 = Button(qsyframe,text="<10<", width=5)
d500 = Button(qsyframe,text="<500<", width=5)
d100 = Button(qsyframe,text="<100<", width=5)
d1000 = Button(qsyframe,text="<1000<", width=5)

ptt.bind('<Button-1>',lambda evt, val = 1: pttaction(val))
ptt.bind('<ButtonRelease-1>',lambda evt, val=0: pttaction(val))

tune.bind('<Button-1>',lambda evt, val = float(10): starttuning(val))

splsu.bind('<Button-1>',lambda evt, val = float(.00001): startspinningt(val))
splsu.bind('<ButtonRelease-1>',stopspinningt)
splsd.bind('<Button-1>',lambda evt, val = float(-.00001): startspinningt(val))
splsd.bind('<ButtonRelease-1>',stopspinningt)

u1000.bind('<Button-1>',lambda evt, val = float(.001): startspinning(val))
u1000.bind('<ButtonRelease-1>',stopspinning)
u500.bind('<Button-1>',lambda evt, val = float(.0005): startspinning(val))
u500.bind('<ButtonRelease-1>',stopspinning)
u100.bind('<Button-1>',lambda evt, val = float(.0001): startspinning(val))
u100.bind('<ButtonRelease-1>',stopspinning)
u10.bind('<Button-1>',lambda evt, val = float(.00001): startspinning(val))
u10.bind('<ButtonRelease-1>',stopspinning)
d10.bind('<Button-1>',lambda evt, val = float(-.00001): startspinning(val))
d10.bind('<ButtonRelease-1>',stopspinning)
d100.bind('<Button-1>',lambda evt, val = float(-.0001): startspinning(val))
d100.bind('<ButtonRelease-1>',stopspinning)
d500.bind('<Button-1>',lambda evt, val = float(-.0005): startspinning(val))
d500.bind('<ButtonRelease-1>',stopspinning)
d1000.bind('<Button-1>',lambda evt, val = float(-.001): startspinning(val))
d1000.bind('<ButtonRelease-1>',stopspinning)

rr = 2
cc = 1
qqsym={}
qqmen={}
qqsv={}
dummy=""
quickqsyframeleg=Frame(quickqsyframe)
quickqsyframeleg.grid(row=1,column=1,columnspan=10)
Label(quickqsyframeleg, text="Quick QSY, E/Extra, A/Advanced, G/General, T/Tech, t/Tech CW Only, N/Novice, n/Novice CW Only").grid(row=1,column=1)
Label(quickqsyframeleg, text="CW", bg="red").grid(row=1,column=2)
Label(quickqsyframeleg, text="end CW / begin Phone", bg="yellow").grid(row=1,column=3)
Label(quickqsyframeleg, text="Phone", bg="green").grid(row=1,column=4)

hover(quickqsyframeleg,"This area is the legend for Quick QSY.  Hopefully, it closely mimics the band plan.")

# QUICK QSY buttons construction
for qq in qqsy:
	if (qq[0] == "dd"):
		qqsv[qq[1]]=StringVar(quickqsyframe)
		qqsv[qq[1]].set(qq[1])
		qqsym[qq[1]]=OptionMenu(quickqsyframe,qqsv[qq[1]],qq[1])
		qqsym[qq[1]].grid(row=rr,column=cc)
		hover(qqsym[qq[1]],"Press and hold to choose one of the frequencies in the list.")
		cc = cc + 1
		qqmen[qq[1]]=qqsym[qq[1]].children["menu"]
		for qfreq in qq:
			if (qfreq == qq[0] or qfreq == qq[1]):
				continue
			zz=lambda mkr=qfreq: QUICKQSY(mkr)
			qqmen[qq[1]].add_command(label=qfreq, command=zz)

	if (qq[0] == "bb"):
		bb=Button(quickqsyframe,\
		text=qq[1].replace('<F>',str('%6.4f' % float(qq[2]))), \
		command=lambda mkr = qq[2]: QUICKQSY(mkr), \
		width=14, pady=0 , bg=qq[3]
		)
		bb.grid(row=rr,column=cc)
		hover(bb,"Press to QSY to "+bb['text'])
		cc = cc + 1
	if (qq[0] == "lb"):
		ll=Label(quickqsyframe,\
		text=qq[1])
		ll.grid(row=rr,column=cc)
		hover(ll,"This is just a band label.  It's not very interesting.")
		cc = cc + 1
	if (qq[0] == "sep"):
		rr = rr + 1
		cc = 1
	

d1000.pack(side=LEFT)
d500.pack(side=LEFT)
d100.pack(side=LEFT)
d10.pack(side=LEFT) 
spinnything.pack(side=LEFT)
u1000.pack(side=RIGHT)
u500.pack(side=RIGHT)
u100.pack(side=RIGHT)
u10.pack(side=RIGHT)

hover(u1000,"Press to change frequency, or hold to spin the knob.")
hover(u500,"Press to change frequency, or hold to spin the knob.")
hover(u100,"Press to change frequency, or hold to spin the knob.")
hover(u10,"Press to change frequency, or hold to spin the knob.")
hover(d1000,"Press to change frequency, or hold to spin the knob.")
hover(d500,"Press to change frequency, or hold to spin the knob.")
hover(d100,"Press to change frequency, or hold to spin the knob.")
hover(d10,"Press to change frequency, or hold to spin the knob.")


ifreqframe.grid(row=1,column=1,columnspan=3)

ifreq.grid(row=1,rowspan=3,column=1,columnspan=2)
itfreq.grid(row=2,column=3,columnspan=2)
splu.grid(row=1,column=5)
vspl.grid(row=2,column=5)
spld.grid(row=3,column=5)
splsd.grid(row=3,column=3)
splsu.grid(row=3,column=4)
spllb.grid(row=1,column=3,columnspan=2)

butframe.grid(row=1,column=4,rowspan=3)
dialbutframe.grid(row=2,column=1,columnspan=3)

clar.grid(    row=1,column=1,rowspan=1)
freq.grid(    row=1,column=2,rowspan=1)
dlock.grid(   row=1,column=3,rowspan=1)

tune.grid(    row=1, column=4, rowspan=1)
ptt.grid(    row=1, column=5, rowspan=1)

hover(ifreq,"You can enter frequency in MHz here, then hit the QSY button to go there.")
hover(itfreq,"You can enter frequency in MHz here, then hit the QSY button to go there.")
hover(freq,"This button sends the above frequency to the radio.")
hover(butframe,"This is a group of the Yaesu Radio buttons.")
hover(clar,"This lets you turn on the CLAR on the radio, but the program doesn't track its status.")
hover(dlock,"This locks ONLY the physical knob on the radio to prevent accidental QSY.")
hover(vspl,"Unbind transmit VFO from main VFO (fake split)")
hover(splu,"Transmit up 1KHz when unbound (fake split)")
hover(spld,"Transmit down 1KHz when unbound (fake split)")

# FRAMES LAYOUT
qsyframe.grid(row=3,column=1,columnspan=3,sticky='EW')
cwframe.grid(row=4,column=1,columnspan=4,sticky='EW')
keysframe.grid(row=5,column=1,columnspan=4,sticky='EW')
macroframe.grid(row=6,column=1,columnspan=4,sticky='EW')
quickqsyframe.grid(row=7,column=1,columnspan=4,sticky='EW')
helpframe.grid(row=8,column=1,columnspan=4,sticky='EW')

# HELP LABEL
hlabel.grid(row=1,column=1)

# CW KEYING
clrb.grid(row=1,column=1)
clr.grid(row=1,column=2)
qcw.grid(row=1,column=3)
bcw.grid(row=1,column=4)
scw.grid(row=1,column=5)
lcw.grid(row=1,column=6)
cwinput.grid(row=1,column=7, columnspan=2)
lwpm.grid(row=1,column=9)
iwpm.grid(row=1,column=10)
lqueue.grid(row=2,column=1)
queue.grid(row=2,column=2,columnspan=9)

# CALLSIGNS
lmycall.grid(row=1,column=1)
imycall.grid(row=1,column=2)
lothercall.grid(row=1,column=3)
iothercall.grid(row=1,column=4)
lnotes.grid(row=1,column=5)

hover(imycall,"Enter YOUR call here and it will be used in macros as <C>.")
hover(iothercall,"Enter OTHER call here and it will be used in macros as <I>.")
hover(iwpm,"Enter words per minute to send here.")

# UPPER RIGHT RADIO BUTTONS
vfoab.grid(   row=1,column=2,rowspan=1)
split.grid(   row=1,column=3,rowspan=1)
mrvfo.grid(   row=1,column=4,rowspan=1)
vmswap.grid(  row=2,column=2,rowspan=1)
vtom.grid(    row=2,column=3,rowspan=1)
mtov.grid(    row=2,column=4,rowspan=1)
banddn.grid(   row=3,column=3,rowspan=1)
bandup.grid(   row=3,column=4,rowspan=1)
dn500k.grid(   row=4,column=3,rowspan=1)
up500k.grid(   row=4,column=4,rowspan=1)
datelab.grid( row=5,column=1,columnspan=4)

hover(vfoab,"Switch between VFO A and B on the radio.  Program won't know the radio's frequency at this point.")
hover(split,"Transmit on the other VFO, whichever it is.  Program won't know the radio's frequency at this point.")
hover(mrvfo,"Switch between VFO and MEM on the radio.  Program won't know the radio's frequency at this point.")
hover(vmswap,"Swap the contents of VFO and MEM on the radio.  Program won't know the radio's frequency at this point.")
hover(vtom,"Write VFO into current MEM on the radio.  Program won't know the radio's frequency at this point.")
hover(mtov,"Write MEM into Current VFO on the radio.  Program won't know the radio's frequency at this point.")
hover(banddn,"Go down to the next ham band.  Position of 500k step switch does not matter.")
hover(bandup,"Go up to the next ham band.  Position of 500k step switch does not matter.")
hover(dn500k,"Go down 500 KHz.  Position of 500k step switch does not matter.")
hover(up500k,"Go up 500 KHz.  Position of 500k step switch does not matter.")

hover(qsyframe,"This is the VFO area.")
hover(cwframe,"This is the CW sending area.")
hover(keysframe,"KEYS FRAME")
hover(macroframe,"Right click in this area between buttons to make a new button.  Right click an already existing button to edit it.")
hover(quickqsyframe,"This area has the Quick QSY buttons.  Radio will immediately go there.")
hover(helpframe,"This area is for helpful help message hovering.")

ReadCfg()
ser = serial.Serial(
	port=serport,
	baudrate=4800,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_TWO,
	bytesize=serial.EIGHTBITS,
	timeout=1,
	xonxoff=0,
	rtscts=0,
	dsrdtr=0
)
ifreq.delete(0,END)
ifreq.insert(0,str('%7.5f' % (rxfreq)))
itfreq.insert(0,str('%7.5f' % (rxfreq)))
iwpm.insert(0,wpm)
imycall.insert(0,mycall)
QSY()

root.geometry(geom)
startclock()

##root.bind("<Enter>",eventbark)
##root.bind("<Leave>",eventbark)
root.mainloop()

