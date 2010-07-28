from PyQt4 import QtGui,QtCore
import imaplib,base64,thread,os
#If there's dbus, we can use freedesktop notifications
try:
	import dbus
	dbusExists = True
except ImportError:
	dbusExists = False
	print "Can't use dbus notifications, falling back to Qt."
configFile = ".gmail-notifierrc"

def stripTags(string):
	import re
	pattern = re.compile(r'<[^<]*?>')
	return pattern.sub('',string)

class SysTrayIcon(QtGui.QSystemTrayIcon):

	username, password = None,None
	checkerStarted = False
	iconPixmap,throbberPixmap = None,None

	# This way we can call paint events from outside the main thread
	throbberStart = QtCore.pyqtSignal()
	throbberStop = QtCore.pyqtSignal()
	messageCountSignal = QtCore.pyqtSignal(int)
	settingsSignal = QtCore.pyqtSignal()

	def __init__(self, icon, parent=None):
		QtGui.QSystemTrayIcon.__init__(self,icon,parent)
		menu = QtGui.QMenu(parent)
		self.iconPixmap = QtGui.QPixmap("icon.png") #Keep these in memory
		self.throbberPixmap = QtGui.QPixmap("spinner.gif")

		self.readConfig()

		#showNotificationAction = QtGui.QAction("Show notification",parent)
		checkAction = QtGui.QAction("Check mail",parent)
		settingsAction = QtGui.QAction("Settings...",parent)
		quitAction = QtGui.QAction("Quit",parent)

		#self.connect(self,QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),self.check)
		self.connect(checkAction,QtCore.SIGNAL("triggered()"),self.check)
		self.connect(settingsAction,QtCore.SIGNAL("triggered()"),self.settings)
		self.connect(quitAction,QtCore.SIGNAL("triggered()"),self.quit)

		menu.setTitle("Gmail Notifier")
		menu.setDefaultAction(checkAction)
		menu.addAction(checkAction)
		menu.addAction(settingsAction)
		menu.addSeparator()
		menu.addAction(quitAction)

		self.setContextMenu(menu)

		self.check() # Check now and every 5 minutes
		timer = QtCore.QTimer(self)
		self.connect(timer,QtCore.SIGNAL("timeout()"),self.check)
		timer.start(5 * 60 * 1000) # 5 minutes

	def showNotification(self,reason,title="Gmail Notifier"):
		if dbusExists: # For the awesome freedesktop standard notifications
			cwd = os.getcwd()
			bus = dbus.SessionBus()
			noteObject = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
			noteIface = dbus.Interface(noteObject, 'org.freedesktop.Notifications')
			noteIface.Notify("Gmail Notifier", 0, cwd+"/icon.png", str(title), str(reason),[],{}, -1)
		else:
			self.showMessage(str(title),str(reason))

	def tCheck(self):
		self.throbberStart.emit()

		mail = imaplib.IMAP4_SSL("imap.gmail.com")
		count = 0

		try:
			mail.login(self.username,self.password)
			mail.select() # Defaults to 'INBOX'
			typ,data = mail.search(None, 'UNSEEN')
			for message in data[0].split():
				typ,data = mail.fetch(message, '(BODY.PEEK[HEADER.FIELDS (from)]<6.56> BODY.PEEK[HEADER.FIELDS (subject)]<9.56> BODY.PEEK[1]<0.200>)') # IMAP Magic
				msgString = "<b>Subject:</b> "+data[0][1].strip()+"\n"\
					+"<b>From:</b> "+data[1][1].strip()+"\n"+stripTags(data[2][1].decode("utf_8","ignore")).strip()
				self.showNotification(msgString,"New Message")
				count += 1
			mail.logout()
		except:
			self.settingsSignal.connect(self.settings)
			self.settingsSignal.emit()

		self.throbberStop.emit()
		self.messageCountSignal.emit(count)
		self.checkerStarted = False

	def check(self): # We don't want to hold up the gui for slow internet crap
		if not self.checkerStarted:
			if self.username is not None:
				self.throbberStart.connect(self.showThrobber)
				self.throbberStop.connect(self.hideThrobber)
				self.messageCountSignal.connect(self.updateMessageCount)
				self.checkerStarted = True
				thread.start_new_thread(self.tCheck,())
			else:
				self.readConfig()

	def updateMessageCount(self, count):
		if count > 0:
			newPixmap = QtGui.QPixmap(self.iconPixmap)
			painter = QtGui.QPainter(newPixmap)
			painter.drawText(0,0,36,36,QtCore.Qt.AlignCenter,str(count))
			self.setIcon(QtGui.QIcon(newPixmap))
			painter.end()
		else:
			self.setIcon(QtGui.QIcon(self.iconPixmap))

	def showThrobber(self):
		newPixmap = QtGui.QPixmap(self.iconPixmap)
		painter = QtGui.QPainter(newPixmap)
		painter.drawPixmap(9,9,self.throbberPixmap)
		self.setIcon(QtGui.QIcon(newPixmap))
		painter.end()

	def hideThrobber(self):
		self.setIcon(QtGui.QIcon(self.iconPixmap))

	def readConfig(self):
		try:
			f = open(configFile,'r')
			self.username = str(base64.b64decode(f.readline())).strip()
			self.password = str(base64.b64decode(f.readline())).strip()
			f.close()
			self.check()
		except IOError:
			self.settings()

	def settings(self):
		self.parent().savedSettingsSignal.connect(self.readConfig)
		self.parent().show()

	def quit(self):
		exit(0)