# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_main_window(object):
    def setupUi(self, main_window):
        if not main_window.objectName():
            main_window.setObjectName(u"main_window")
        main_window.resize(1112, 871)
        main_window.setStyleSheet(u"")
        self.main_page = QWidget(main_window)
        self.main_page.setObjectName(u"main_page")
        self.main_page.setEnabled(True)
        self.horizontalLayout_2 = QHBoxLayout(self.main_page)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.main_widget = QStackedWidget(self.main_page)
        self.main_widget.setObjectName(u"main_widget")
        self.main_widget.setEnabled(True)
        self.main_widget.setMinimumSize(QSize(0, 30))
        self.main_widget.setBaseSize(QSize(0, 0))
        self.main = QWidget()
        self.main.setObjectName(u"main")
        self.main.setAutoFillBackground(False)
        self.verticalLayout_23 = QVBoxLayout(self.main)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.verticalSpacer = QSpacerItem(20, 372, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_23.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(18, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.to_converter = QCommandLinkButton(self.main)
        self.to_converter.setObjectName(u"to_converter")

        self.horizontalLayout.addWidget(self.to_converter)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.to_sapr = QCommandLinkButton(self.main)
        self.to_sapr.setObjectName(u"to_sapr")
        self.to_sapr.setEnabled(False)

        self.horizontalLayout.addWidget(self.to_sapr)

        self.horizontalSpacer_55 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_55)

        self.commandLinkButton_8 = QCommandLinkButton(self.main)
        self.commandLinkButton_8.setObjectName(u"commandLinkButton_8")
        self.commandLinkButton_8.setEnabled(False)

        self.horizontalLayout.addWidget(self.commandLinkButton_8)

        self.horizontalSpacer_56 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_56)

        self.to_options = QCommandLinkButton(self.main)
        self.to_options.setObjectName(u"to_options")
        self.to_options.setEnabled(True)
        self.to_options.setCheckable(False)
        self.to_options.setChecked(False)
        self.to_options.setAutoExclusive(False)

        self.horizontalLayout.addWidget(self.to_options)

        self.horizontalSpacer_57 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_57)


        self.verticalLayout_23.addLayout(self.horizontalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 372, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_23.addItem(self.verticalSpacer_2)

        self.main_widget.addWidget(self.main)
        self.options = QWidget()
        self.options.setObjectName(u"options")
        self.horizontalLayout_49 = QHBoxLayout(self.options)
        self.horizontalLayout_49.setObjectName(u"horizontalLayout_49")
        self.horizontalSpacer_33 = QSpacerItem(76, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_49.addItem(self.horizontalSpacer_33)

        self.root_tab_widget = QTabWidget(self.options)
        self.root_tab_widget.setObjectName(u"root_tab_widget")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.root_tab_widget.addTab(self.tab_3, "")
        self.options1 = QWidget()
        self.options1.setObjectName(u"options1")
        self.horizontalLayout_11 = QHBoxLayout(self.options1)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.converter_options = QTabWidget(self.options1)
        self.converter_options.setObjectName(u"converter_options")
        self.converter_options.setStyleSheet(u"")
        self.options_tab_machines = QWidget()
        self.options_tab_machines.setObjectName(u"options_tab_machines")
        self.horizontalLayout_51 = QHBoxLayout(self.options_tab_machines)
        self.horizontalLayout_51.setObjectName(u"horizontalLayout_51")
        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.add_machine_list_0 = QListWidget(self.options_tab_machines)
        self.add_machine_list_0.setObjectName(u"add_machine_list_0")

        self.verticalLayout_19.addWidget(self.add_machine_list_0)

        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName(u"horizontalLayout_36")
        self.remove_button_0 = QPushButton(self.options_tab_machines)
        self.remove_button_0.setObjectName(u"remove_button_0")

        self.horizontalLayout_36.addWidget(self.remove_button_0)

        self.add_button_0 = QPushButton(self.options_tab_machines)
        self.add_button_0.setObjectName(u"add_button_0")

        self.horizontalLayout_36.addWidget(self.add_button_0)


        self.verticalLayout_19.addLayout(self.horizontalLayout_36)


        self.horizontalLayout_51.addLayout(self.verticalLayout_19)

        self.line_13 = QFrame(self.options_tab_machines)
        self.line_13.setObjectName(u"line_13")
        self.line_13.setFrameShape(QFrame.VLine)
        self.line_13.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_51.addWidget(self.line_13)

        self.verticalLayout_24 = QVBoxLayout()
        self.verticalLayout_24.setObjectName(u"verticalLayout_24")
        self.horizontalLayout_50 = QHBoxLayout()
        self.horizontalLayout_50.setObjectName(u"horizontalLayout_50")
        self.horizontalSpacer_53 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_50.addItem(self.horizontalSpacer_53)

        self.label_20 = QLabel(self.options_tab_machines)
        self.label_20.setObjectName(u"label_20")
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_20.setFont(font)

        self.horizontalLayout_50.addWidget(self.label_20)

        self.horizontalSpacer_54 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_50.addItem(self.horizontalSpacer_54)


        self.verticalLayout_24.addLayout(self.horizontalLayout_50)

        self.groupBox_7 = QGroupBox(self.options_tab_machines)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.verticalLayout_39 = QVBoxLayout(self.groupBox_7)
        self.verticalLayout_39.setObjectName(u"verticalLayout_39")
        self.horizontalLayout_71 = QHBoxLayout()
        self.horizontalLayout_71.setObjectName(u"horizontalLayout_71")
        self.label_21 = QLabel(self.groupBox_7)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_71.addWidget(self.label_21)

        self.lineEdit_10 = QLineEdit(self.groupBox_7)
        self.lineEdit_10.setObjectName(u"lineEdit_10")
        self.lineEdit_10.setReadOnly(True)

        self.horizontalLayout_71.addWidget(self.lineEdit_10)

        self.add_machine_input = QToolButton(self.groupBox_7)
        self.add_machine_input.setObjectName(u"add_machine_input")

        self.horizontalLayout_71.addWidget(self.add_machine_input)


        self.verticalLayout_39.addLayout(self.horizontalLayout_71)

        self.horizontalLayout_70 = QHBoxLayout()
        self.horizontalLayout_70.setObjectName(u"horizontalLayout_70")
        self.label_22 = QLabel(self.groupBox_7)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout_70.addWidget(self.label_22)

        self.lineEdit_21 = QLineEdit(self.groupBox_7)
        self.lineEdit_21.setObjectName(u"lineEdit_21")
        self.lineEdit_21.setReadOnly(True)

        self.horizontalLayout_70.addWidget(self.lineEdit_21)

        self.add_machine_output = QToolButton(self.groupBox_7)
        self.add_machine_output.setObjectName(u"add_machine_output")

        self.horizontalLayout_70.addWidget(self.add_machine_output)


        self.verticalLayout_39.addLayout(self.horizontalLayout_70)


        self.verticalLayout_24.addWidget(self.groupBox_7)

        self.line_14 = QFrame(self.options_tab_machines)
        self.line_14.setObjectName(u"line_14")
        self.line_14.setFrameShape(QFrame.HLine)
        self.line_14.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_24.addWidget(self.line_14)

        self.groupBox_8 = QGroupBox(self.options_tab_machines)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.verticalLayout_21 = QVBoxLayout(self.groupBox_8)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.horizontalLayout_37 = QHBoxLayout()
        self.horizontalLayout_37.setObjectName(u"horizontalLayout_37")
        self.label_23 = QLabel(self.groupBox_8)
        self.label_23.setObjectName(u"label_23")

        self.horizontalLayout_37.addWidget(self.label_23)

        self.lineEdit_11 = QLineEdit(self.groupBox_8)
        self.lineEdit_11.setObjectName(u"lineEdit_11")

        self.horizontalLayout_37.addWidget(self.lineEdit_11)


        self.verticalLayout_21.addLayout(self.horizontalLayout_37)

        self.horizontalLayout_38 = QHBoxLayout()
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.label_24 = QLabel(self.groupBox_8)
        self.label_24.setObjectName(u"label_24")

        self.horizontalLayout_38.addWidget(self.label_24)

        self.lineEdit_12 = QLineEdit(self.groupBox_8)
        self.lineEdit_12.setObjectName(u"lineEdit_12")

        self.horizontalLayout_38.addWidget(self.lineEdit_12)


        self.verticalLayout_21.addLayout(self.horizontalLayout_38)

        self.horizontalLayout_39 = QHBoxLayout()
        self.horizontalLayout_39.setObjectName(u"horizontalLayout_39")
        self.label_25 = QLabel(self.groupBox_8)
        self.label_25.setObjectName(u"label_25")

        self.horizontalLayout_39.addWidget(self.label_25)

        self.lineEdit_13 = QLineEdit(self.groupBox_8)
        self.lineEdit_13.setObjectName(u"lineEdit_13")

        self.horizontalLayout_39.addWidget(self.lineEdit_13)


        self.verticalLayout_21.addLayout(self.horizontalLayout_39)


        self.verticalLayout_24.addWidget(self.groupBox_8)

        self.line_15 = QFrame(self.options_tab_machines)
        self.line_15.setObjectName(u"line_15")
        self.line_15.setFrameShape(QFrame.HLine)
        self.line_15.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_24.addWidget(self.line_15)

        self.groupBox_9 = QGroupBox(self.options_tab_machines)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.verticalLayout_22 = QVBoxLayout(self.groupBox_9)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.horizontalLayout_40 = QHBoxLayout()
        self.horizontalLayout_40.setObjectName(u"horizontalLayout_40")
        self.label_26 = QLabel(self.groupBox_9)
        self.label_26.setObjectName(u"label_26")

        self.horizontalLayout_40.addWidget(self.label_26)

        self.lineEdit_14 = QLineEdit(self.groupBox_9)
        self.lineEdit_14.setObjectName(u"lineEdit_14")

        self.horizontalLayout_40.addWidget(self.lineEdit_14)


        self.verticalLayout_22.addLayout(self.horizontalLayout_40)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName(u"horizontalLayout_41")
        self.label_27 = QLabel(self.groupBox_9)
        self.label_27.setObjectName(u"label_27")

        self.horizontalLayout_41.addWidget(self.label_27)

        self.lineEdit_15 = QLineEdit(self.groupBox_9)
        self.lineEdit_15.setObjectName(u"lineEdit_15")

        self.horizontalLayout_41.addWidget(self.lineEdit_15)


        self.verticalLayout_22.addLayout(self.horizontalLayout_41)

        self.horizontalLayout_42 = QHBoxLayout()
        self.horizontalLayout_42.setObjectName(u"horizontalLayout_42")
        self.label_28 = QLabel(self.groupBox_9)
        self.label_28.setObjectName(u"label_28")

        self.horizontalLayout_42.addWidget(self.label_28)

        self.lineEdit_16 = QLineEdit(self.groupBox_9)
        self.lineEdit_16.setObjectName(u"lineEdit_16")

        self.horizontalLayout_42.addWidget(self.lineEdit_16)


        self.verticalLayout_22.addLayout(self.horizontalLayout_42)


        self.verticalLayout_24.addWidget(self.groupBox_9)

        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName(u"horizontalLayout_43")
        self.label_29 = QLabel(self.options_tab_machines)
        self.label_29.setObjectName(u"label_29")

        self.horizontalLayout_43.addWidget(self.label_29)

        self.lineEdit_17 = QLineEdit(self.options_tab_machines)
        self.lineEdit_17.setObjectName(u"lineEdit_17")

        self.horizontalLayout_43.addWidget(self.lineEdit_17)


        self.verticalLayout_24.addLayout(self.horizontalLayout_43)


        self.horizontalLayout_51.addLayout(self.verticalLayout_24)

        self.converter_options.addTab(self.options_tab_machines, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_3 = QVBoxLayout(self.tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tabWidget_2 = QTabWidget(self.tab)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.add_operation_list = QWidget()
        self.add_operation_list.setObjectName(u"add_operation_list")
        self.horizontalLayout_35 = QHBoxLayout(self.add_operation_list)
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.label_18 = QLabel(self.add_operation_list)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setFont(font)

        self.verticalLayout_16.addWidget(self.label_18)

        self.listWidget = QListWidget(self.add_operation_list)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_16.addWidget(self.listWidget)


        self.horizontalLayout_35.addLayout(self.verticalLayout_16)

        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.move_right_0 = QPushButton(self.add_operation_list)
        self.move_right_0.setObjectName(u"move_right_0")
        icon = QIcon()
        icon.addFile(u"../../gui/static/img/arrow-right.png", QSize(), QIcon.Normal, QIcon.Off)
        self.move_right_0.setIcon(icon)

        self.verticalLayout_18.addWidget(self.move_right_0)

        self.move_left_0 = QPushButton(self.add_operation_list)
        self.move_left_0.setObjectName(u"move_left_0")
        icon1 = QIcon()
        icon1.addFile(u"../../gui/static/img/arrow-left.png", QSize(), QIcon.Normal, QIcon.Off)
        self.move_left_0.setIcon(icon1)

        self.verticalLayout_18.addWidget(self.move_left_0)


        self.horizontalLayout_35.addLayout(self.verticalLayout_18)

        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.label_19 = QLabel(self.add_operation_list)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setFont(font)

        self.verticalLayout_17.addWidget(self.label_19)

        self.listWidget_2 = QListWidget(self.add_operation_list)
        self.listWidget_2.setObjectName(u"listWidget_2")

        self.verticalLayout_17.addWidget(self.listWidget_2)


        self.horizontalLayout_35.addLayout(self.verticalLayout_17)

        self.tabWidget_2.addTab(self.add_operation_list, "")
        self.add_operation_first = QWidget()
        self.add_operation_first.setObjectName(u"add_operation_first")
        self.horizontalLayout_10 = QHBoxLayout(self.add_operation_first)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.stackedWidget_2 = QStackedWidget(self.add_operation_first)
        self.stackedWidget_2.setObjectName(u"stackedWidget_2")
        self.stackedWidget_2.setFrameShape(QFrame.NoFrame)
        self.stackedWidget_2.setFrameShadow(QFrame.Plain)
        self.add_operation_first1 = QWidget()
        self.add_operation_first1.setObjectName(u"add_operation_first1")
        self.verticalLayout_5 = QVBoxLayout(self.add_operation_first1)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_9)

        self.label_2 = QLabel(self.add_operation_first1)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(18)
        font1.setBold(True)
        font1.setWeight(75)
        self.label_2.setFont(font1)
        self.label_2.setTextFormat(Qt.AutoText)
        self.label_2.setIndent(-1)

        self.horizontalLayout_5.addWidget(self.label_2)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_10)


        self.verticalLayout_5.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)

        self.checkBox = QCheckBox(self.add_operation_first1)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setChecked(True)

        self.horizontalLayout_4.addWidget(self.checkBox)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)


        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.line = QFrame(self.add_operation_first1)
        self.line.setObjectName(u"line")
        self.line.setLayoutDirection(Qt.LeftToRight)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_7)

        self.safetly_operations_select_label = QLabel(self.add_operation_first1)
        self.safetly_operations_select_label.setObjectName(u"safetly_operations_select_label")

        self.horizontalLayout_3.addWidget(self.safetly_operations_select_label)

        self.safetly_operations_select = QComboBox(self.add_operation_first1)
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.addItem("")
        self.safetly_operations_select.setObjectName(u"safetly_operations_select")

        self.horizontalLayout_3.addWidget(self.safetly_operations_select)

        self.operations_select = QLabel(self.add_operation_first1)
        self.operations_select.setObjectName(u"operations_select")

        self.horizontalLayout_3.addWidget(self.operations_select)

        self.operations_select_2 = QComboBox(self.add_operation_first1)
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.addItem("")
        self.operations_select_2.setObjectName(u"operations_select_2")
        self.operations_select_2.setEnabled(True)
        self.operations_select_2.setFrame(True)

        self.horizontalLayout_3.addWidget(self.operations_select_2)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_8)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_11)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)

        self.commandLinkButton = QCommandLinkButton(self.add_operation_first1)
        self.commandLinkButton.setObjectName(u"commandLinkButton")
        self.commandLinkButton.setEnabled(False)

        self.verticalLayout_4.addWidget(self.commandLinkButton)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_12)


        self.verticalLayout_5.addLayout(self.horizontalLayout_6)

        self.stackedWidget_2.addWidget(self.add_operation_first1)
        self.page_6 = QWidget()
        self.page_6.setObjectName(u"page_6")
        self.verticalLayout_13 = QVBoxLayout(self.page_6)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_16)

        self.label_14 = QLabel(self.page_6)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font1)

        self.horizontalLayout_27.addWidget(self.label_14)

        self.horizontalSpacer_42 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_42)


        self.verticalLayout_13.addLayout(self.horizontalLayout_27)

        self.line_11 = QFrame(self.page_6)
        self.line_11.setObjectName(u"line_11")
        self.line_11.setFrameShape(QFrame.HLine)
        self.line_11.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_13.addWidget(self.line_11)

        self.horizontalLayout_28 = QHBoxLayout()
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.horizontalSpacer_43 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_28.addItem(self.horizontalSpacer_43)

        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.label_15 = QLabel(self.page_6)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_26.addWidget(self.label_15)

        self.lineEdit_8 = QLineEdit(self.page_6)
        self.lineEdit_8.setObjectName(u"lineEdit_8")

        self.horizontalLayout_26.addWidget(self.lineEdit_8)


        self.horizontalLayout_28.addLayout(self.horizontalLayout_26)

        self.groupBox_5 = QGroupBox(self.page_6)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy)
        self.layoutWidget = QWidget(self.groupBox_5)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(20, 30, 160, 49))
        self.verticalLayout_20 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.radioButton_3 = QRadioButton(self.layoutWidget)
        self.radioButton_3.setObjectName(u"radioButton_3")
        self.radioButton_3.setChecked(True)

        self.verticalLayout_20.addWidget(self.radioButton_3)

        self.radioButton_10 = QRadioButton(self.layoutWidget)
        self.radioButton_10.setObjectName(u"radioButton_10")

        self.verticalLayout_20.addWidget(self.radioButton_10)


        self.horizontalLayout_28.addWidget(self.groupBox_5)

        self.horizontalSpacer_44 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_28.addItem(self.horizontalSpacer_44)


        self.verticalLayout_13.addLayout(self.horizontalLayout_28)

        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.horizontalSpacer_45 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_45)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalSpacer_13 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_13)

        self.commandLinkButton_6 = QCommandLinkButton(self.page_6)
        self.commandLinkButton_6.setObjectName(u"commandLinkButton_6")
        self.commandLinkButton_6.setEnabled(False)

        self.verticalLayout_12.addWidget(self.commandLinkButton_6)

        self.verticalSpacer_14 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_14)


        self.horizontalLayout_29.addLayout(self.verticalLayout_12)

        self.horizontalSpacer_46 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_46)


        self.verticalLayout_13.addLayout(self.horizontalLayout_29)

        self.stackedWidget_2.addWidget(self.page_6)
        self.page_7 = QWidget()
        self.page_7.setObjectName(u"page_7")
        self.verticalLayout_15 = QVBoxLayout(self.page_7)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.horizontalSpacer_51 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_33.addItem(self.horizontalSpacer_51)

        self.label_17 = QLabel(self.page_7)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setFont(font1)

        self.horizontalLayout_33.addWidget(self.label_17)

        self.horizontalSpacer_52 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_33.addItem(self.horizontalSpacer_52)


        self.verticalLayout_15.addLayout(self.horizontalLayout_33)

        self.line_12 = QFrame(self.page_7)
        self.line_12.setObjectName(u"line_12")
        self.line_12.setFrameShape(QFrame.HLine)
        self.line_12.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_15.addWidget(self.line_12)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.horizontalSpacer_47 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_47)

        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.label_16 = QLabel(self.page_7)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_31.addWidget(self.label_16)

        self.lineEdit_9 = QLineEdit(self.page_7)
        self.lineEdit_9.setObjectName(u"lineEdit_9")

        self.horizontalLayout_31.addWidget(self.lineEdit_9)


        self.horizontalLayout_30.addLayout(self.horizontalLayout_31)

        self.groupBox_6 = QGroupBox(self.page_7)
        self.groupBox_6.setObjectName(u"groupBox_6")
        sizePolicy.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy)
        self.groupBox_6.setMinimumSize(QSize(0, 0))
        self.layoutWidget1 = QWidget(self.groupBox_6)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(10, 30, 160, 49))
        self.verticalLayout_40 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_40.setObjectName(u"verticalLayout_40")
        self.verticalLayout_40.setContentsMargins(0, 0, 0, 0)
        self.radioButton_11 = QRadioButton(self.layoutWidget1)
        self.radioButton_11.setObjectName(u"radioButton_11")
        self.radioButton_11.setChecked(True)

        self.verticalLayout_40.addWidget(self.radioButton_11)

        self.radioButton_12 = QRadioButton(self.layoutWidget1)
        self.radioButton_12.setObjectName(u"radioButton_12")

        self.verticalLayout_40.addWidget(self.radioButton_12)


        self.horizontalLayout_30.addWidget(self.groupBox_6)

        self.horizontalSpacer_48 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_48)


        self.verticalLayout_15.addLayout(self.horizontalLayout_30)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.horizontalSpacer_49 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_32.addItem(self.horizontalSpacer_49)

        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalSpacer_15 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_14.addItem(self.verticalSpacer_15)

        self.commandLinkButton_7 = QCommandLinkButton(self.page_7)
        self.commandLinkButton_7.setObjectName(u"commandLinkButton_7")
        self.commandLinkButton_7.setEnabled(False)

        self.verticalLayout_14.addWidget(self.commandLinkButton_7)

        self.verticalSpacer_16 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_14.addItem(self.verticalSpacer_16)


        self.horizontalLayout_32.addLayout(self.verticalLayout_14)

        self.horizontalSpacer_50 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_32.addItem(self.horizontalSpacer_50)


        self.verticalLayout_15.addLayout(self.horizontalLayout_32)

        self.stackedWidget_2.addWidget(self.page_7)
        self.numerate_page = QWidget()
        self.numerate_page.setObjectName(u"numerate_page")
        self.verticalLayout_6 = QVBoxLayout(self.numerate_page)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_13)

        self.label_3 = QLabel(self.numerate_page)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)

        self.horizontalLayout_7.addWidget(self.label_3)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_14)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.line_2 = QFrame(self.numerate_page)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_6.addWidget(self.line_2)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_15)

        self.label_4 = QLabel(self.numerate_page)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_8.addWidget(self.label_4)

        self.lineEdit = QLineEdit(self.numerate_page)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout_8.addWidget(self.lineEdit)

        self.line_10 = QFrame(self.numerate_page)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFrameShape(QFrame.VLine)
        self.line_10.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_8.addWidget(self.line_10)

        self.label_5 = QLabel(self.numerate_page)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_8.addWidget(self.label_5)

        self.lineEdit_2 = QLineEdit(self.numerate_page)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.horizontalLayout_8.addWidget(self.lineEdit_2)

        self.horizontalSpacer_17 = QSpacerItem(28, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_17)


        self.verticalLayout_6.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_18)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_6)

        self.commandLinkButton_2 = QCommandLinkButton(self.numerate_page)
        self.commandLinkButton_2.setObjectName(u"commandLinkButton_2")

        self.verticalLayout.addWidget(self.commandLinkButton_2)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_5)


        self.horizontalLayout_9.addLayout(self.verticalLayout)

        self.horizontalSpacer_19 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_19)


        self.verticalLayout_6.addLayout(self.horizontalLayout_9)

        self.stackedWidget_2.addWidget(self.numerate_page)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.verticalLayout_7 = QVBoxLayout(self.page_3)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_27 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_27)

        self.label_6 = QLabel(self.page_3)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)

        self.horizontalLayout_13.addWidget(self.label_6)

        self.horizontalSpacer_21 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_21)


        self.verticalLayout_7.addLayout(self.horizontalLayout_13)

        self.line_4 = QFrame(self.page_3)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_7.addWidget(self.line_4)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalSpacer_24 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_24)

        self.groupBox = QGroupBox(self.page_3)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setBaseSize(QSize(500, 0))
        self.layoutWidget2 = QWidget(self.groupBox)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(20, 30, 160, 49))
        self.verticalLayout_42 = QVBoxLayout(self.layoutWidget2)
        self.verticalLayout_42.setObjectName(u"verticalLayout_42")
        self.verticalLayout_42.setContentsMargins(0, 0, 0, 0)
        self.radioButton = QRadioButton(self.layoutWidget2)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setChecked(True)

        self.verticalLayout_42.addWidget(self.radioButton)

        self.radioButton_2 = QRadioButton(self.layoutWidget2)
        self.radioButton_2.setObjectName(u"radioButton_2")

        self.verticalLayout_42.addWidget(self.radioButton_2)


        self.horizontalLayout_16.addWidget(self.groupBox)

        self.line_3 = QFrame(self.page_3)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_16.addWidget(self.line_3)

        self.groupBox_2 = QGroupBox(self.page_3)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy1)
        self.groupBox_2.setMinimumSize(QSize(0, 300))
        self.layoutWidget3 = QWidget(self.groupBox_2)
        self.layoutWidget3.setObjectName(u"layoutWidget3")
        self.layoutWidget3.setGeometry(QRect(60, 30, 65, 49))
        self.verticalLayout_41 = QVBoxLayout(self.layoutWidget3)
        self.verticalLayout_41.setObjectName(u"verticalLayout_41")
        self.verticalLayout_41.setContentsMargins(0, 0, 0, 0)
        self.radioButton_4 = QRadioButton(self.layoutWidget3)
        self.radioButton_4.setObjectName(u"radioButton_4")

        self.verticalLayout_41.addWidget(self.radioButton_4)

        self.radioButton_5 = QRadioButton(self.layoutWidget3)
        self.radioButton_5.setObjectName(u"radioButton_5")

        self.verticalLayout_41.addWidget(self.radioButton_5)


        self.horizontalLayout_16.addWidget(self.groupBox_2)

        self.horizontalSpacer_20 = QSpacerItem(18, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_20)


        self.verticalLayout_7.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_7 = QLabel(self.page_3)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_14.addWidget(self.label_7)

        self.lineEdit_3 = QLineEdit(self.page_3)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.horizontalLayout_14.addWidget(self.lineEdit_3)


        self.horizontalLayout_17.addLayout(self.horizontalLayout_14)

        self.horizontalSpacer_22 = QSpacerItem(18, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_22)

        self.line_5 = QFrame(self.page_3)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_17.addWidget(self.line_5)

        self.horizontalSpacer_30 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_30)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_8 = QLabel(self.page_3)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_15.addWidget(self.label_8)

        self.lineEdit_4 = QLineEdit(self.page_3)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.horizontalLayout_15.addWidget(self.lineEdit_4)


        self.horizontalLayout_17.addLayout(self.horizontalLayout_15)


        self.verticalLayout_7.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalSpacer_25 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_25)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_7)

        self.commandLinkButton_3 = QCommandLinkButton(self.page_3)
        self.commandLinkButton_3.setObjectName(u"commandLinkButton_3")
        self.commandLinkButton_3.setEnabled(False)

        self.verticalLayout_2.addWidget(self.commandLinkButton_3)

        self.verticalSpacer_8 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_8)


        self.horizontalLayout_12.addLayout(self.verticalLayout_2)

        self.horizontalSpacer_26 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_26)


        self.verticalLayout_7.addLayout(self.horizontalLayout_12)

        self.stackedWidget_2.addWidget(self.page_3)
        self.page_4 = QWidget()
        self.page_4.setObjectName(u"page_4")
        self.verticalLayout_9 = QVBoxLayout(self.page_4)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalSpacer_28 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_28)

        self.label_9 = QLabel(self.page_4)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font1)

        self.horizontalLayout_18.addWidget(self.label_9)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_23)


        self.verticalLayout_9.addLayout(self.horizontalLayout_18)

        self.line_7 = QFrame(self.page_4)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_9.addWidget(self.line_7)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.horizontalSpacer_29 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_34.addItem(self.horizontalSpacer_29)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_11 = QLabel(self.page_4)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_19.addWidget(self.label_11)

        self.lineEdit_6 = QLineEdit(self.page_4)
        self.lineEdit_6.setObjectName(u"lineEdit_6")

        self.horizontalLayout_19.addWidget(self.lineEdit_6)


        self.horizontalLayout_34.addLayout(self.horizontalLayout_19)

        self.line_6 = QFrame(self.page_4)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_34.addWidget(self.line_6)

        self.groupBox_3 = QGroupBox(self.page_4)
        self.groupBox_3.setObjectName(u"groupBox_3")
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.layoutWidget4 = QWidget(self.groupBox_3)
        self.layoutWidget4.setObjectName(u"layoutWidget4")
        self.layoutWidget4.setGeometry(QRect(10, 30, 160, 49))
        self.verticalLayout_43 = QVBoxLayout(self.layoutWidget4)
        self.verticalLayout_43.setObjectName(u"verticalLayout_43")
        self.verticalLayout_43.setContentsMargins(0, 0, 0, 0)
        self.radioButton_6 = QRadioButton(self.layoutWidget4)
        self.radioButton_6.setObjectName(u"radioButton_6")

        self.verticalLayout_43.addWidget(self.radioButton_6)

        self.radioButton_7 = QRadioButton(self.layoutWidget4)
        self.radioButton_7.setObjectName(u"radioButton_7")

        self.verticalLayout_43.addWidget(self.radioButton_7)


        self.horizontalLayout_34.addWidget(self.groupBox_3)

        self.horizontalSpacer_31 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_34.addItem(self.horizontalSpacer_31)


        self.verticalLayout_9.addLayout(self.horizontalLayout_34)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalSpacer_34 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_34)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_9)

        self.commandLinkButton_4 = QCommandLinkButton(self.page_4)
        self.commandLinkButton_4.setObjectName(u"commandLinkButton_4")
        self.commandLinkButton_4.setEnabled(False)

        self.verticalLayout_8.addWidget(self.commandLinkButton_4)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_10)


        self.horizontalLayout_20.addLayout(self.verticalLayout_8)

        self.horizontalSpacer_35 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_35)


        self.verticalLayout_9.addLayout(self.horizontalLayout_20)

        self.stackedWidget_2.addWidget(self.page_4)
        self.page_5 = QWidget()
        self.page_5.setObjectName(u"page_5")
        self.verticalLayout_11 = QVBoxLayout(self.page_5)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.horizontalSpacer_36 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_36)

        self.label_10 = QLabel(self.page_5)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font1)

        self.horizontalLayout_21.addWidget(self.label_10)

        self.horizontalSpacer_37 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_37)


        self.verticalLayout_11.addLayout(self.horizontalLayout_21)

        self.line_9 = QFrame(self.page_5)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_11.addWidget(self.line_9)

        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.horizontalSpacer_40 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_25.addItem(self.horizontalSpacer_40)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.label_12 = QLabel(self.page_5)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_23.addWidget(self.label_12)

        self.lineEdit_5 = QLineEdit(self.page_5)
        self.lineEdit_5.setObjectName(u"lineEdit_5")

        self.horizontalLayout_23.addWidget(self.lineEdit_5)


        self.horizontalLayout_25.addLayout(self.horizontalLayout_23)

        self.groupBox_4 = QGroupBox(self.page_5)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        self.layoutWidget5 = QWidget(self.groupBox_4)
        self.layoutWidget5.setObjectName(u"layoutWidget5")
        self.layoutWidget5.setGeometry(QRect(10, 30, 92, 49))
        self.verticalLayout_44 = QVBoxLayout(self.layoutWidget5)
        self.verticalLayout_44.setObjectName(u"verticalLayout_44")
        self.verticalLayout_44.setContentsMargins(0, 0, 0, 0)
        self.radioButton_8 = QRadioButton(self.layoutWidget5)
        self.radioButton_8.setObjectName(u"radioButton_8")

        self.verticalLayout_44.addWidget(self.radioButton_8)

        self.radioButton_9 = QRadioButton(self.layoutWidget5)
        self.radioButton_9.setObjectName(u"radioButton_9")

        self.verticalLayout_44.addWidget(self.radioButton_9)


        self.horizontalLayout_25.addWidget(self.groupBox_4)

        self.line_8 = QFrame(self.page_5)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.VLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_25.addWidget(self.line_8)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.label_13 = QLabel(self.page_5)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_24.addWidget(self.label_13)

        self.lineEdit_7 = QLineEdit(self.page_5)
        self.lineEdit_7.setObjectName(u"lineEdit_7")

        self.horizontalLayout_24.addWidget(self.lineEdit_7)


        self.horizontalLayout_25.addLayout(self.horizontalLayout_24)

        self.horizontalSpacer_41 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_25.addItem(self.horizontalSpacer_41)


        self.verticalLayout_11.addLayout(self.horizontalLayout_25)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.horizontalSpacer_38 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer_38)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalSpacer_11 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_11)

        self.commandLinkButton_5 = QCommandLinkButton(self.page_5)
        self.commandLinkButton_5.setObjectName(u"commandLinkButton_5")

        self.verticalLayout_10.addWidget(self.commandLinkButton_5)

        self.verticalSpacer_12 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_12)


        self.horizontalLayout_22.addLayout(self.verticalLayout_10)

        self.horizontalSpacer_39 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer_39)


        self.verticalLayout_11.addLayout(self.horizontalLayout_22)

        self.stackedWidget_2.addWidget(self.page_5)

        self.horizontalLayout_10.addWidget(self.stackedWidget_2)

        self.tabWidget_2.addTab(self.add_operation_first, "")

        self.verticalLayout_3.addWidget(self.tabWidget_2)

        self.converter_options.addTab(self.tab, "")
        self.options_merging = QWidget()
        self.options_merging.setObjectName(u"options_merging")
        self.verticalLayout_27 = QVBoxLayout(self.options_merging)
        self.verticalLayout_27.setObjectName(u"verticalLayout_27")
        self.horizontalLayout_45 = QHBoxLayout()
        self.horizontalLayout_45.setObjectName(u"horizontalLayout_45")
        self.horizontalSpacer_3 = QSpacerItem(168, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_45.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_44 = QHBoxLayout()
        self.horizontalLayout_44.setObjectName(u"horizontalLayout_44")
        self.label_30 = QLabel(self.options_merging)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setFont(font1)

        self.horizontalLayout_44.addWidget(self.label_30)

        self.comboBox = QComboBox(self.options_merging)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setFont(font1)

        self.horizontalLayout_44.addWidget(self.comboBox)


        self.horizontalLayout_45.addLayout(self.horizontalLayout_44)

        self.horizontalSpacer_4 = QSpacerItem(418, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_45.addItem(self.horizontalSpacer_4)


        self.verticalLayout_27.addLayout(self.horizontalLayout_45)

        self.line_17 = QFrame(self.options_merging)
        self.line_17.setObjectName(u"line_17")
        self.line_17.setFrameShape(QFrame.HLine)
        self.line_17.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_27.addWidget(self.line_17)

        self.horizontalLayout_48 = QHBoxLayout()
        self.horizontalLayout_48.setObjectName(u"horizontalLayout_48")
        self.line_18 = QFrame(self.options_merging)
        self.line_18.setObjectName(u"line_18")
        self.line_18.setFrameShape(QFrame.VLine)
        self.line_18.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_48.addWidget(self.line_18)

        self.verticalLayout_26 = QVBoxLayout()
        self.verticalLayout_26.setObjectName(u"verticalLayout_26")
        self.label_32 = QLabel(self.options_merging)
        self.label_32.setObjectName(u"label_32")
        self.label_32.setFont(font1)

        self.verticalLayout_26.addWidget(self.label_32)

        self.listWidget_9 = QListWidget(self.options_merging)
        QListWidgetItem(self.listWidget_9)
        self.listWidget_9.setObjectName(u"listWidget_9")
        self.listWidget_9.setDragEnabled(True)
        self.listWidget_9.setDragDropMode(QAbstractItemView.DragDrop)
        self.listWidget_9.setDefaultDropAction(Qt.MoveAction)

        self.verticalLayout_26.addWidget(self.listWidget_9)

        self.horizontalLayout_47 = QHBoxLayout()
        self.horizontalLayout_47.setObjectName(u"horizontalLayout_47")
        self.remove_button_2 = QPushButton(self.options_merging)
        self.remove_button_2.setObjectName(u"remove_button_2")

        self.horizontalLayout_47.addWidget(self.remove_button_2)

        self.add_button_2 = QPushButton(self.options_merging)
        self.add_button_2.setObjectName(u"add_button_2")

        self.horizontalLayout_47.addWidget(self.add_button_2)


        self.verticalLayout_26.addLayout(self.horizontalLayout_47)

        self.listWidget_7 = QListWidget(self.options_merging)
        QListWidgetItem(self.listWidget_7)
        self.listWidget_7.setObjectName(u"listWidget_7")
        self.listWidget_7.setDragEnabled(True)
        self.listWidget_7.setDragDropMode(QAbstractItemView.DragDrop)
        self.listWidget_7.setDefaultDropAction(Qt.MoveAction)

        self.verticalLayout_26.addWidget(self.listWidget_7)


        self.horizontalLayout_48.addLayout(self.verticalLayout_26)


        self.verticalLayout_27.addLayout(self.horizontalLayout_48)

        self.converter_options.addTab(self.options_merging, "")

        self.horizontalLayout_11.addWidget(self.converter_options)

        self.root_tab_widget.addTab(self.options1, "")
        self.convertation_tab = QWidget()
        self.convertation_tab.setObjectName(u"convertation_tab")
        self.converter_launch = QCommandLinkButton(self.convertation_tab)
        self.converter_launch.setObjectName(u"converter_launch")
        self.converter_launch.setGeometry(QRect(370, 540, 185, 41))
        self.lcdNumber = QLCDNumber(self.convertation_tab)
        self.lcdNumber.setObjectName(u"lcdNumber")
        self.lcdNumber.setGeometry(QRect(610, 150, 131, 91))
        self.label = QLabel(self.convertation_tab)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(570, 130, 201, 20))
        self.root_tab_widget.addTab(self.convertation_tab, "")

        self.horizontalLayout_49.addWidget(self.root_tab_widget)

        self.horizontalSpacer_32 = QSpacerItem(76, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_49.addItem(self.horizontalSpacer_32)

        self.main_widget.addWidget(self.options)

        self.horizontalLayout_2.addWidget(self.main_widget)

        main_window.setCentralWidget(self.main_page)
        self.menubar = QMenuBar(main_window)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1112, 21))
        main_window.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(main_window)
        self.statusbar.setObjectName(u"statusbar")
        main_window.setStatusBar(self.statusbar)

        self.retranslateUi(main_window)

        self.main_widget.setCurrentIndex(1)
        self.root_tab_widget.setCurrentIndex(0)
        self.converter_options.setCurrentIndex(2)
        self.tabWidget_2.setCurrentIndex(1)
        self.stackedWidget_2.setCurrentIndex(6)


        QMetaObject.connectSlotsByName(main_window)
    # setupUi

    def retranslateUi(self, main_window):
        main_window.setWindowTitle(QCoreApplication.translate("main_window", u"MainWindow", None))
        self.to_converter.setText(QCoreApplication.translate("main_window", u"\u0410\u0432\u0442\u043e-\u043a\u043e\u043d\u0432\u0435\u0440\u0442\u0435\u0440", None))
        self.to_sapr.setText(QCoreApplication.translate("main_window", u"\u0421\u0410\u041f\u0420", None))
        self.commandLinkButton_8.setText(QCoreApplication.translate("main_window", u"\u041a\u0430\u043b\u044c\u043a\u0443\u043b\u044f\u0442\u043e\u0440 \u0440\u0435\u0436\u0438\u043c\u043e\u0432", None))
        self.to_options.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.root_tab_widget.setTabText(self.root_tab_widget.indexOf(self.tab_3), QCoreApplication.translate("main_window", u"\u0413\u043b\u0430\u0432\u043d\u0430\u044f", None))
        self.remove_button_0.setText("")
        self.add_button_0.setText("")
        self.label_20.setText(QCoreApplication.translate("main_window", u"\u0425\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("main_window", u"\u041a\u043e\u0440\u043d\u0435\u0432\u043e\u0439 \u043a\u0430\u0442\u0430\u043b\u043e\u0433", None))
        self.label_21.setText(QCoreApplication.translate("main_window", u"\u0412\u0445\u043e\u0434\u043d\u043e\u0439", None))
        self.add_machine_input.setText(QCoreApplication.translate("main_window", u"...", None))
        self.label_22.setText(QCoreApplication.translate("main_window", u"\u0412\u044b\u0445\u043e\u0434\u043d\u043e\u0439", None))
        self.add_machine_output.setText(QCoreApplication.translate("main_window", u"...", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("main_window", u"\u0420\u0430\u0441\u0445\u043e\u0434 \u043f\u043e \u043e\u0441\u044f\u043c (\u041c\u041c)", None))
        self.label_23.setText(QCoreApplication.translate("main_window", u"X", None))
        self.label_24.setText(QCoreApplication.translate("main_window", u"Y", None))
        self.label_25.setText(QCoreApplication.translate("main_window", u"Z", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("main_window", u"\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e-\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u043f\u043e\u0434\u0430\u0447\u0438 \u043f\u043e \u043e\u0441\u044f\u043c (F/\u041c\u0438\u043d)", None))
        self.label_26.setText(QCoreApplication.translate("main_window", u"X", None))
        self.label_27.setText(QCoreApplication.translate("main_window", u"Y", None))
        self.label_28.setText(QCoreApplication.translate("main_window", u"Z", None))
        self.label_29.setText(QCoreApplication.translate("main_window", u"\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e-\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u043e\u0431\u043e\u0440\u043e\u0442\u044b \u0448\u043f\u0438\u043d\u0434\u0435\u043b\u044f", None))
        self.converter_options.setTabText(self.converter_options.indexOf(self.options_tab_machines), QCoreApplication.translate("main_window", u"\u0421\u0442\u0430\u043d\u043a\u0438", None))
        self.label_18.setText(QCoreApplication.translate("main_window", u"\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0435", None))
        self.move_right_0.setText("")
        self.move_left_0.setText("")
        self.label_19.setText(QCoreApplication.translate("main_window", u"\u0412\u044b\u043a\u043b\u044e\u0447\u0435\u043d\u043d\u044b\u0435", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.add_operation_list), QCoreApplication.translate("main_window", u"\u0421\u043f\u0438\u0441\u043e\u043a \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0439", None))
        self.label_2.setText(QCoreApplication.translate("main_window", u"\u0412\u044b\u0431\u043e\u0440 \u0442\u0438\u043f\u0430 \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0438", None))
        self.checkBox.setText(QCoreApplication.translate("main_window", u"\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 \u0440\u0435\u0436\u0438\u043c", None))
        self.safetly_operations_select_label.setText(QCoreApplication.translate("main_window", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0437\u0430\u0434\u0430\u0447\u0438", None))
        self.safetly_operations_select.setItemText(0, QCoreApplication.translate("main_window", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0442\u0438\u043f \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0438", None))
        self.safetly_operations_select.setItemText(1, QCoreApplication.translate("main_window", u"\u041d\u0443\u043c\u0435\u0440\u0430\u0446\u0438\u044f \u043a\u0430\u0434\u0440\u043e\u0432", None))
        self.safetly_operations_select.setItemText(2, QCoreApplication.translate("main_window", u"\u041f\u0435\u0440\u0435\u0431\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u043b\u0451\u0442", None))
        self.safetly_operations_select.setItemText(3, QCoreApplication.translate("main_window", u"\u0421\u0434\u0432\u0438\u043d\u0443\u0442\u044c \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443", None))
        self.safetly_operations_select.setItemText(4, QCoreApplication.translate("main_window", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.safetly_operations_select.setItemText(5, QCoreApplication.translate("main_window", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.safetly_operations_select.setItemText(6, QCoreApplication.translate("main_window", u"\u0417\u0430\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.safetly_operations_select.setItemText(7, QCoreApplication.translate("main_window", u"\u0420\u0430\u0441\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))

        self.operations_select.setText(QCoreApplication.translate("main_window", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0437\u0430\u0434\u0430\u0447\u0438", None))
        self.operations_select_2.setItemText(0, QCoreApplication.translate("main_window", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0442\u0438\u043f \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0438", None))
        self.operations_select_2.setItemText(1, QCoreApplication.translate("main_window", u"\u041d\u0443\u043c\u0435\u0440\u0430\u0446\u0438\u044f \u043a\u0430\u0434\u0440\u043e\u0432", None))
        self.operations_select_2.setItemText(2, QCoreApplication.translate("main_window", u"\u0417\u0430\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0438\u043c\u0432\u043e\u043b\u044b", None))
        self.operations_select_2.setItemText(3, QCoreApplication.translate("main_window", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.operations_select_2.setItemText(4, QCoreApplication.translate("main_window", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.operations_select_2.setItemText(5, QCoreApplication.translate("main_window", u"\u0417\u0430\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.operations_select_2.setItemText(6, QCoreApplication.translate("main_window", u"\u0420\u0430\u0441\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))

        self.commandLinkButton.setText(QCoreApplication.translate("main_window", u"\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043a \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044e", None))
        self.label_14.setText(QCoreApplication.translate("main_window", u"\u0417\u0430\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.label_15.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0439\u0442\u0438", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("main_window", u"\u0418\u0441\u043a\u043e\u043c\u044b\u0439", None))
        self.radioButton_3.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u0442", None))
        self.radioButton_10.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e", None))
        self.commandLinkButton_6.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.label_17.setText(QCoreApplication.translate("main_window", u"\u0420\u0430\u0441\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.label_16.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0439\u0442\u0438", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("main_window", u"\u0418\u0441\u043a\u043e\u043c\u044b\u0439", None))
        self.radioButton_11.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u0442", None))
        self.radioButton_12.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e", None))
        self.commandLinkButton_7.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.label_3.setText(QCoreApplication.translate("main_window", u"\u041d\u0443\u043c\u0435\u0440\u0430\u0446\u0438\u044f \u0423\u041f", None))
        self.label_4.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0447\u0430\u0442\u044c \u0441 ", None))
        self.lineEdit.setText(QCoreApplication.translate("main_window", u"0", None))
        self.label_5.setText(QCoreApplication.translate("main_window", u"\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435", None))
        self.lineEdit_2.setText(QCoreApplication.translate("main_window", u"9999", None))
        self.commandLinkButton_2.setText(QCoreApplication.translate("main_window", u"\u041f\u0440\u043e\u043d\u0443\u043c\u0435\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0443", None))
        self.label_6.setText(QCoreApplication.translate("main_window", u"\u0412\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.groupBox.setTitle(QCoreApplication.translate("main_window", u"\u0415\u0441\u043b\u0438 \u0438\u0441\u043a\u043e\u043c\u044b\u0439", None))
        self.radioButton.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u0442", None))
        self.radioButton_2.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("main_window", u"\u0412\u0441\u0442\u0430\u0432\u0438\u0442\u044c", None))
        self.radioButton_4.setText(QCoreApplication.translate("main_window", u"\u041f\u0435\u0440\u0435\u0434", None))
        self.radioButton_5.setText(QCoreApplication.translate("main_window", u"\u041f\u043e\u0441\u043b\u0435", None))
        self.label_7.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0439\u0442\u0438", None))
        self.label_8.setText(QCoreApplication.translate("main_window", u"\u0412\u0441\u0442\u0430\u0432\u0438\u0442\u044c", None))
        self.commandLinkButton_3.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.label_9.setText(QCoreApplication.translate("main_window", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.label_11.setText(QCoreApplication.translate("main_window", u"\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b", None))
        self.groupBox_3.setTitle("")
        self.radioButton_6.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u0442", None))
        self.radioButton_7.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e", None))
        self.commandLinkButton_4.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.label_10.setText(QCoreApplication.translate("main_window", u"\u0417\u0430\u043c\u0435\u043d\u0438\u0442\u044c \u043a\u0430\u0434\u0440", None))
        self.label_12.setText(QCoreApplication.translate("main_window", u"\u041d\u0430\u0439\u0442\u0438", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("main_window", u"\u0415\u0441\u043b\u0438 \u0438\u0441\u0445\u043e\u0434\u043d\u044b\u0439", None))
        self.radioButton_8.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u0442", None))
        self.radioButton_9.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442", None))
        self.label_13.setText(QCoreApplication.translate("main_window", u"\u0417\u0430\u043c\u0435\u043d\u0438\u0442\u044c", None))
        self.commandLinkButton_5.setText(QCoreApplication.translate("main_window", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.add_operation_first), QCoreApplication.translate("main_window", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", None))
        self.converter_options.setTabText(self.converter_options.indexOf(self.tab), QCoreApplication.translate("main_window", u"\u041e\u043f\u0435\u0440\u0430\u0446\u0438\u0438", None))
        self.label_30.setText(QCoreApplication.translate("main_window", u"\u0421\u0442\u0430\u043d\u043e\u043a", None))
        self.label_32.setText(QCoreApplication.translate("main_window", u"\u041e\u043f\u0435\u0440\u0430\u0446\u0438\u0438", None))

        __sortingEnabled = self.listWidget_9.isSortingEnabled()
        self.listWidget_9.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget_9.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("main_window", u"\u044b\u0432\u0430\u044b\u0432\u0430\u044b\u0432\u0430", None));
        self.listWidget_9.setSortingEnabled(__sortingEnabled)

        self.remove_button_2.setText("")
        self.add_button_2.setText("")

        __sortingEnabled1 = self.listWidget_7.isSortingEnabled()
        self.listWidget_7.setSortingEnabled(False)
        ___qlistwidgetitem1 = self.listWidget_7.item(0)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("main_window", u"\u044b\u0432\u0430\u044b\u0432\u0430\u044b\u0432\u0430", None));
        self.listWidget_7.setSortingEnabled(__sortingEnabled1)

        self.converter_options.setTabText(self.converter_options.indexOf(self.options_merging), QCoreApplication.translate("main_window", u"\u041f\u0440\u0438\u0432\u044f\u0437\u0430\u0442\u044c", None))
        self.root_tab_widget.setTabText(self.root_tab_widget.indexOf(self.options1), QCoreApplication.translate("main_window", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.converter_launch.setText(QCoreApplication.translate("main_window", u"\u041f\u0443\u0441\u043a", None))
        self.label.setText(QCoreApplication.translate("main_window", u"\u0412\u0441\u0435\u0433\u043e \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0439 \u043d\u0430\u0434 \u0444\u0430\u0439\u043b\u0430\u043c\u0438 \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c", None))
        self.root_tab_widget.setTabText(self.root_tab_widget.indexOf(self.convertation_tab), QCoreApplication.translate("main_window", u"\u041a\u043e\u043d\u0432\u0435\u0440\u0442\u0430\u0446\u0438\u044f", None))
    # retranslateUi

