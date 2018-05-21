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

from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, \
    QLabel, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QFormLayout, \
    QVBoxLayout, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap

from client import WebSocketClient
from quamash import QEventLoop

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

        ip = QLabel(_('Server IP:  '))
        ip_edit = QLineEdit()
        port = QLabel(_('Server Port:  '))
        port_edit = QLineEdit()
        user = QLabel(_('Username:  '))
        user_edit = QLineEdit()
        passwd = QLabel(_('Password:  '))
        passwd_edit = QLineEdit()
        passwd_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        remember = QCheckBox(_('Remember password'))
        remember.stateChanged.connect(partial(self.remember_passwd, remember))

        # load conf and initilize components
        self.dconf = {}
        if os.path.exists(conf):
            self.dconf = conf_load(self.parser, conf)
            ip_edit.setText(self.dconf['ip'])
            port_edit.setText(self.dconf['port'])
            user_edit.setText(self.dconf['username'])
            remember.setChecked(True if 'remember_passwd' in self.dconf.keys(
            ) and self.dconf['remember_passwd'] == 'True' else False)
            if remember.isChecked():
                passwd_edit.setText(self.dconf['passwd'])

        login_btn = QPushButton(_('Login'))
        self.login_wait = QLabel(
            _(
                '\nType the all information above Form.\nClick the "Login" button to continue!'
            ))
        self.login_wait.setStyleSheet("QLabel{color:rgb(70,140,200,240);}")
        login_btn.clicked[bool].connect(
            partial(
                self.login, {
                    'ip': ip_edit,
                    'port': port_edit,
                    'username': user_edit,
                    'passwd': passwd_edit
                }))

        form = QFormLayout()
        form.addRow(ip, ip_edit)
        form.addRow(port, port_edit)
        form.addRow(user, user_edit)
        form.addRow(passwd, passwd_edit)

        check_box = QHBoxLayout()
        check_box.addStretch(1)
        check_box.addWidget(remember)
        check_box.addStretch(1)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        btn_box.addWidget(login_btn)
        btn_box.addStretch(1)

        label_box = QHBoxLayout()
        label_box.addStretch(1)
        label_box.addWidget(self.login_wait)
        label_box.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(check_box)
        vbox.addLayout(btn_box)
        vbox.addLayout(label_box)

        self.setLayout(vbox)
        self.show()

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

                    'ip': _('The server IP'),
                    'port': _('The server port'),
                    'username': _('The username'),
                    'passwd': _('The password')
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
            # process login
            # self.start_login(d)
            # loop = asyncio.get_event_loop()
            import threading
            t = threading.Thread(target=self.start_login, args=(d,))
            t.start()

    def start_login(self, d):
        wsc = WebSocketClient(d['ip'], d['port'], d['username'], d['passwd'])
        wsc.add_handler('login_succeed', self.login_succeed)
        wsc.add_handler('login_failed', self.login_failed)
        wsc.add_handler('recevied_notify', self.recevied_notify)
        wsc.start()

    def login_succeed(self):
        # login succeed
        self.tray.show()
        self.setVisible(False)

    def login_failed(self):
        self.login_wait.setText(_('\nLogin Failed!\n\n'
                        'To fix this issue, please try:\n'
                        '1.Make sure your network is fine\n'
                        '2.Make sure the \'IP\' and \'PORT\' of server is right\n'
                        '3.Check the username and password is right or not'))
        self.login_wait.setStyleSheet("QLabel{color:rgb(240,0,0,240);}")

    def recevied_notify(self, msg):
        self.tray.show_msg(msg)

    def remember_passwd(self, checkbox):
        if checkbox.isChecked():
            self.dconf['remember_passwd'] = 'True'
        else:
            self.dconf['remember_passwd'] = 'False'
            self.dconf.pop('passwd')
        conf_save(self.parser, self.dconf)


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
