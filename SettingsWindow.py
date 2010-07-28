from PyQt4 import QtGui,QtCore
import imaplib
import base64
configFile = ".gmail-notifierrc"

class SettingsWindow(QtGui.QWidget):
	username,password,save,cancel = None,None,None,None
	savedSettingsSignal = QtCore.pyqtSignal()

	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.setWindowTitle("Settings")
		layout = QtGui.QGridLayout(self)
		self.setLayout(layout)

		self.username = QtGui.QLineEdit()
		self.password = QtGui.QLineEdit()
		self.password.setEchoMode(QtGui.QLineEdit.Password)
		self.save = QtGui.QPushButton("Save")
		self.cancel = QtGui.QPushButton("Cancel")

		try:
			f = open(configFile,'r')
			self.username.setText(str(base64.b64decode(f.readline())))
			self.password.setText(str(base64.b64decode(f.readline())))
			f.close()
		except IOError:
			pass

		layout.addWidget(QtGui.QLabel("Username"),0,0)
		layout.addWidget(self.username,0,1)
		layout.addWidget(QtGui.QLabel("Password"),1,0)
		layout.addWidget(self.password,1,1)
		layout.addWidget(self.save,2,0)
		layout.addWidget(self.cancel,2,1)

		self.connect(self.cancel,QtCore.SIGNAL("clicked()"),self.closeEvent)
		self.connect(self.save,QtCore.SIGNAL("clicked()"),self.saveEvent)

	def saveEvent(self,event=None):
		f = open(configFile,'w')
		f.write(base64.b64encode(str(self.username.text())) + "\n" + base64.b64encode(str(self.password.text())))
		f.close()
		self.savedSettingsSignal.emit()
		self.closeEvent()

	def closeEvent(self,event=None):
		self.hide()
		if event is not None: event.ignore()