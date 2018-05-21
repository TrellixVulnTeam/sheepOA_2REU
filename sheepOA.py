#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: yushuibo
@Copyright (c) 2018 yushuibo. All rights reserved.
@Licence: GPL-2
@Email: hengchen2005@gmail.com
@File: sheepOA.py
@Create: 2018-05-19 13:15:47
@Last Modified: 2018-05-19 13:15:47
@Desc: --
"""

import os
import sys
import locale
import gettext
import webbrowser
from configparser import ConfigParser
from functools import partial

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, \
    QLabel, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QFormLayout, \
    QVBoxLayout, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap

from client import WebSocketClient

base_dir = os.getcwd()
conf = os.path.join(base_dir, 'conf.ini')


def conf_save(parser, dconf):
    """save config to file"""
    parser.remove_section('global')
    parser.add_section('global')
    for k, v in dconf.items():
        parser.set('global', k, v)
    with open(conf, "w") as f:
        parser.write(f)


def conf_load(parser, cf):
    """load config from file"""
    parser.read(cf)
    return dict(parser.items('global'))


class LoginWin(QWidget):
    def __init__(self):
        super(LoginWin, self).__init__()
        self.parser = ConfigParser()
        self.tray = Tray(self)

    def init_ui(self):
        # set default size for root window
        self.resize(350, 200)
        # centered the root window
        self.center()
        # set title
        self.setWindowTitle('SheepOA Client v1.0')

        self.ip = QLabel(_('Server IP:  '))
        self.ip_edit = QLineEdit()
        self.port = QLabel(_('Server Port:  '))
        self.port_edit = QLineEdit()
        self.user = QLabel(_('Username:  '))
        self.user_edit = QLineEdit()
        self.passwd = QLabel(_('Password:  '))
        self.passwd_edit = QLineEdit()
        self.passwd_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.remember = QCheckBox(_('Remember password'))
        self.remember.stateChanged.connect(self.remember_passwd)

        # load conf and initilize components
        self.dconf = {}
        if os.path.exists(conf):
            self.dconf = conf_load(self.parser, conf)
            self.ip_edit.setText(self.dconf['ip'])
            self.port_edit.setText(self.dconf['port'])
            self.user_edit.setText(self.dconf['username'])
            self.remember.setChecked(
                True if 'remember_passwd' in self.dconf.keys()
                and self.dconf['remember_passwd'] == 'True' else False)
            if self.remember.isChecked():
                self.passwd_edit.setText(self.dconf['passwd'])

        self.login_btn = QPushButton(_('Login'))
        self.tip = QLabel(
            _('\nType the all information above Form.\nClick the "Login" button to continue!'
              ))
        self.tip.setStyleSheet("QLabel{color:rgb(70,140,200,240);}")
        self.login_btn.clicked[bool].connect(
            partial(
                self.login, {
                    'ip': self.ip_edit,
                    'port': self.port_edit,
                    'username': self.user_edit,
                    'passwd': self.passwd_edit
                }))

        form = QFormLayout()
        form.addRow(self.ip, self.ip_edit)
        form.addRow(self.port, self.port_edit)
        form.addRow(self.user, self.user_edit)
        form.addRow(self.passwd, self.passwd_edit)

        check_box = QHBoxLayout()
        check_box.addStretch(1)
        check_box.addWidget(self.remember)
        check_box.addStretch(1)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        btn_box.addWidget(self.login_btn)
        btn_box.addStretch(1)

        label_box = QHBoxLayout()
        label_box.addStretch(1)
        label_box.addWidget(self.tip)
        label_box.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(check_box)
        vbox.addLayout(btn_box)
        vbox.addLayout(label_box)

        self.setLayout(vbox)
        self.show()
        self.tray.show()

    def closeEvent(self, event):
        """override default exit event"""
        question(
            _('Question'),
            _('Are you sure to quit?'),
            event=event,
            parent=self)

    def center(self):
        """centered self on screen"""
        # get the root window object
        wroot = self.frameGeometry()
        # get the centered point of the screen
        cpoint = QDesktopWidget().availableGeometry().center()
        # move the root window to center of the screen
        wroot.moveCenter(cpoint)
        self.move(wroot.topLeft())

    def check_form(self, info_dict):
        """check form info is full done"""
        #  self.dconf.clear()
        for k, v in info_dict.items():
            if isinstance(v, str):
                continue
            v = v.text()
            if v:
                self.dconf[k] = v
            else:
                critical(
                    _('Critical'),
                    _('{} can\'t be empty!').format({
                        'ip':
                        _('The server IP'),
                        'port':
                        _('The server port'),
                        'username':
                        _('The username'),
                        'passwd':
                        _('The password')
                    }.get(k)),
                    parent=self)
                return (False, None)
        return (True, self.dconf)

    def login(self, info_dict=None):
        """login handlfer"""
        r, d = self.check_form(info_dict)
        if r and d:
            # save config to file
            conf_save(self.parser, d)
            self.change_status(False)
            # process login
            # self.start_login(d)
            # loop = asyncio.get_event_loop()
            netth = NetThread(d, parent=self)
            netth.login_succeed_signal.connect(self.login_succeed)
            netth.login_failed_signal.connect(self.login_failed)
            netth.recevied_notify_signal.connect(self.recevied_notify)
            netth.start()

    def start_login(self, d):
        wsc = WebSocketClient(d['ip'], d['port'], d['username'], d['passwd'])
        wsc.add_handler('login_succeed', self.login_succeed)
        wsc.add_handler('login_failed', self.login_failed)
        wsc.add_handler('recevied_notify', self.recevied_notify)
        wsc.start()

    def login_succeed(self):
        # login succeed
        self.setVisible(False)

    def login_failed(self):
        information(
            _('Login Failed!'),
            _('To fix this issue, please try:\n'
              '1. Make sure the network of computer is working fine;\n'
              '2. Make sure the \'IP\' and \'PORT\' of server is right;\n'
              '4. Close the firewall of system and try again;\n'
              '3. Check the username and password is right or not.'),
            parent=self)
        self.change_status(True)

    def recevied_notify(self, msg):
        self.tray.show_msg(msg)

    def remember_passwd(self):
        if self.remember.isChecked():
            self.dconf['remember_passwd'] = 'True'
        else:
            self.dconf['remember_passwd'] = 'False'
            self.dconf.pop('passwd')
        conf_save(self.parser, self.dconf)

    def change_status(self, enable=True):
        if enable:
            self.ip_edit.setDisabled(False)
            self.port_edit.setDisabled(False)
            self.user_edit.setDisabled(False)
            self.passwd_edit.setDisabled(False)
            self.remember.setDisabled(False)
            self.login_btn.setDisabled(False)
            self.tip.setText(
                _('\nType the all information above Form.\nClick the "Login" button to continue!'
                  ))
            self.tip.setStyleSheet("QLabel{color:rgb(70,140,200,240);}")
        else:
            self.ip_edit.setDisabled(True)
            self.port_edit.setDisabled(True)
            self.user_edit.setDisabled(True)
            self.passwd_edit.setDisabled(True)
            self.remember.setDisabled(True)
            self.login_btn.setDisabled(True)
            self.tip.setText(_('\nLongin ...'))
            self.tip.setStyleSheet("QLabel{color:rgb(200,0,0,240);}")


class NetThread(QThread):
    login_succeed_signal = pyqtSignal()
    login_failed_signal = pyqtSignal()
    recevied_notify_signal = pyqtSignal(str)

    def __init__(self, dconf, parent=None):
        super(NetThread, self).__init__(parent)
        self.d = dconf

    def run(self):
        wsc = WebSocketClient(self, self.d['ip'], self.d['port'],
                              self.d['username'], self.d['passwd'])
        wsc.start()


# overrid QMessageBox
def question(rtext, info, event=None, parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(_('SheepOA'))
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setText(rtext)
    msg_box.setInformativeText(info)
    msg_box.addButton(_('Yes'), QMessageBox.AcceptRole)
    msg_box.setDefaultButton(
        msg_box.addButton(_('No'), QMessageBox.RejectRole))
    replay = msg_box.exec()
    if replay == QMessageBox.AcceptRole:
        event.accept()
    else:
        event.ignore()


def warning(rtext, info, event=None, parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(_('SheepOA'))
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setText(rtext)
    msg_box.setInformativeText(info)
    msg_box.addButton(_('Yes'), QMessageBox.AcceptRole)
    msg_box.setDefaultButton(
        msg_box.addButton(_('No'), QMessageBox.RejectRole))
    replay = msg_box.exec()
    if replay == QMessageBox.AcceptRole:
        event.accept()
    else:
        event.ignore()


def information(rtext, info, event=None, parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(_('SheepOA'))
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setText(rtext)
    msg_box.setInformativeText(info)
    msg_box.setDefaultButton(
        msg_box.addButton(_('Ok'), QMessageBox.DestructiveRole))
    replay = msg_box.exec()
    if replay == QMessageBox.DestructiveRole:
        event.ignore()


def critical(rtext, info, event=None, parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(_('SheepOA'))
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText(rtext)
    msg_box.setInformativeText(info)
    msg_box.setDefaultButton(
        msg_box.addButton(_('Ok'), QMessageBox.DestructiveRole))
    replay = msg_box.exec()
    if replay == QMessageBox.DestructiveRole:
        event.ignore()


class Tray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super(Tray, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        menu = QMenu()
        # show_action = QAction('Show Msg', self, triggered=self.show_msg)
        quit_action = QAction(_('Quit'), self, triggered=self.quit)
        # menu.addAction(show_action)
        menu.addAction(quit_action)
        self.setContextMenu(menu)
        #  self.activated.connect(self.icon_clicked)
        self.messageClicked.connect(self.msg_click)
        self.setIcon(QIcon('./imgs/icon.ico'))

    def icon_clicked(self, reason):
        if reason == 2 or reason == 3:
            parent = self.parent()
            if parent.isVisible():
                parent.hide()
            else:
                parent.show()

    def show_msg(self, msg):
        icon = QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Information)
        self.url = msg.content
        self.showMessage(
            _('Notify!'),
            _('A new message from {}.\nClicked this to view detail of:\n{}'. \
            format(msg._from, msg.content)), icon)

    def msg_click(self):
        # fork a webbroser object to open url
        webbrowser.open(self.url, new=2)

    def quit(self):
        self.setVisible(False)
        sys.exit()


if __name__ == '__main__':
    # i18n
    gettext.find("main", localedir="locale", all=True)
    if locale.getdefaultlocale()[0] == 'zh_CN':
        t = gettext.translation(
            'main', 'locale', languages=['cn'], fallback=True)
    else:
        t = gettext.translation(
            'main', 'locale', languages=['en'], fallback=True)
    _ = t.gettext

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(QPixmap('./imgs/icon.ico')))
    login_win = LoginWin()
    login_win.init_ui()
    sys.exit(app.exec_())
