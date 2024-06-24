from PyQt6 import QtWidgets, QtCore, QtGui
from src.models.model_apps import Model, ModelApps
from src.controllers.control_anypoint import AnypointConfig
from .views.setup_ui import Ui_Setup
from .constants import *

# for the setup dialog
class SetupDialog(QtWidgets.QDialog):
    def __init__(self, model_apps: ModelApps):
        super().__init__()
        
        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.accept_function)
        self.ui.cancelButton.clicked.connect(self.reject_function)
        
        self.model = Model()
        self.model_apps = model_apps
        self.anypoint_config = AnypointConfig(self.ui)

        # setup and gracefully close the slots and signals of ModelApps (image_result and signal_image_original)
        update_original_label_slot = lambda img: self.update_label_image(self.ui.label_image_original, img)
        update_result_label_slot = lambda img: self.update_label_image(self.ui.label_image_result, img)
        self.setup_original_signal(update_original_label_slot, self.model_apps.signal_image_original)
        self.setup_result_signal(update_result_label_slot, self.model_apps.image_result)

        self.ui.m1Button.setChecked(True)
        self.ui.modeSelectGroup.buttonClicked.connect(self.mode_select_clicked)
        self.mode_select_clicked()

        self.ui.checkBox.stateChanged.connect(self.checkbox_click)
        self.ui.checkBox.setChecked(True)
        self.checkbox_click()

        self.set_resolution_sources()
        
        self.ui.topButton.clicked.connect(self.onclick_anypoint)
        self.ui.belowButton.clicked.connect(self.onclick_anypoint)
        self.ui.centerButton.clicked.connect(self.onclick_anypoint)
        self.ui.leftButton.clicked.connect(self.onclick_anypoint)
        self.ui.rightButton.clicked.connect(self.onclick_anypoint)
        
        self.model_apps.alpha_beta.connect(self.alpha_beta_from_coordinate)
        self.model_apps.value_coordinate.connect(self.set_value_coordinate)
        self.model_apps.state_rubberband = False

        # setup mouse events
        self.ui.label_image_original.mouseReleaseEvent = self.label_original_mouse_release_event
        self.ui.label_image_original.mouseMoveEvent = self.label_original_mouse_move_event
        
        # With this event, for some reason it's occuring some bugs.
        # self.ui.label_image_original.mousePressEvent = self.label_original_mouse_press_event
        
        self.ui.label_image_original.mousePressEvent = self.label_original_mouse_move_event
        self.ui.label_image_original.leaveEvent = self.label_original_mouse_leave_event
        self.ui.label_image_original.mouseDoubleClickEvent = self.label_original_mouse_double_click_event

        self.ui.doubleSpinBox_alpha.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_beta.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_roll.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_zoom.valueChanged.connect(self.change_properties_anypoint)

        self.set_stylesheet()

    def set_stylesheet(self):
        # self.ui.label_title_original.setStyleSheet(self.model.style_label_title())
        # self.ui.label_title_image_result.setStyleSheet(self.model.style_label_title())
        self.ui.label_image_original.setStyleSheet(self.model.style_label())
        self.ui.label_image_result.setStyleSheet(self.model.style_label())
        self.ui.topButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.belowButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.rightButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.leftButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.centerButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.okButton.setStyleSheet(self.model.style_pushbutton())
        self.ui.cancelButton.setStyleSheet(self.model.style_pushbutton())

    def change_properties_anypoint(self):
        self.model_apps.state_rubberband = False
        if self.ui.m1Button.isChecked():
            self.anypoint_config.change_properties_mode_1()
            self.model_apps.create_maps_anypoint_mode_1()
        else:
            self.anypoint_config.change_properties_mode_2()
            self.model_apps.create_maps_anypoint_mode_2()
        self.model_apps.update_file_config()
    
    def set_value_coordinate(self, coordinate: list[float]):
        self.ui.label_pos_x.setText(str(coordinate[0]))
        self.ui.label_pos_y.setText(str(coordinate[1]))

    # set up Anypoint Mode 1 or 2 with state_recent_view = "AnypointView"
    def mode_select_clicked(self):
        if self.ui.m1Button.isChecked():
            self.ui.doubleSpinBox_roll.hide()
            self.ui.labelRoll.hide()
            self.ui.labelAlpha.setText('Alpha:')
            self.ui.labelBeta.setText('Beta:')
            self.model_apps.state_recent_view = "AnypointView"
            self.model_apps.change_anypoint_mode = "mode_1"
            self.model_apps.create_maps_anypoint_mode_1()
            self.anypoint_config.showing_config_mode_1()
        else:
            self.ui.doubleSpinBox_roll.show()
            self.ui.labelRoll.show()
            self.ui.labelAlpha.setText('Pitch:')
            self.ui.labelBeta.setText('Yaw:')
            self.model_apps.state_recent_view = "AnypointView"
            self.model_apps.change_anypoint_mode = "mode_2"
            self.model_apps.create_maps_anypoint_mode_2()
            self.anypoint_config.showing_config_mode_2()
        self.model_apps.update_properties_config_when_change_view_mode()
    
    def checkbox_click(self):
        self.model_apps.set_draw_polygon = True if self.ui.checkBox.isChecked() else False
        
    def alpha_beta_from_coordinate(self, alpha_beta: list[float]):
        self.ui.doubleSpinBox_alpha.blockSignals(True)
        self.ui.doubleSpinBox_beta.blockSignals(True)
        
        if any(elem is None for elem in alpha_beta):
            self.ui.doubleSpinBox_alpha.setValue(0)
            self.ui.doubleSpinBox_beta.setValue(0)
        else:
            self.ui.doubleSpinBox_alpha.setValue(round(alpha_beta[0], 2))
            self.ui.doubleSpinBox_beta.setValue(round(alpha_beta[1], 2))
            
        self.ui.doubleSpinBox_alpha.blockSignals(False)
        self.ui.doubleSpinBox_beta.blockSignals(False)

    def onclick_anypoint(self):
        if self.ui.m1Button.isChecked():
            if self.sender().objectName() == 'topButton':
                self.model_apps.set_alpha_beta(75, 0)
            elif self.sender().objectName() == 'belowButton':
                self.model_apps.set_alpha_beta(75, 180)
            elif self.sender().objectName() == 'centerButton':
                self.model_apps.set_alpha_beta(0, 0)
            elif self.sender().objectName() == 'leftButton':
                self.model_apps.set_alpha_beta(75, -90)
            elif self.sender().objectName() == 'rightButton':
                self.model_apps.set_alpha_beta(75, 90)
                
            self.anypoint_config.showing_config_mode_1()
            self.model_apps.create_maps_anypoint_mode_1()
            
        else:
            if self.sender().objectName() == 'topButton':
                self.model_apps.set_alpha_beta(75, 0)
            elif self.sender().objectName() == 'belowButton':
                self.model_apps.set_alpha_beta(-75, 0)
            elif self.sender().objectName() == 'centerButton':
                self.model_apps.set_alpha_beta(0, 0)
            elif self.sender().objectName() == 'leftButton':
                self.model_apps.set_alpha_beta(0, -75)
            elif self.sender().objectName() == 'rightButton':
                self.model_apps.set_alpha_beta(0, 75)
                
            self.anypoint_config.showing_config_mode_2()
            self.model_apps.create_maps_anypoint_mode_2()
            
        self.model_apps.state_rubberband = False
        self.model_apps.update_file_config()

    def set_resolution_sources(self):
        self.ui.comboBox_resolution_sources.blockSignals(True)
        self.ui.comboBox_resolution_sources.clear()
        self.ui.comboBox_resolution_sources.blockSignals(False)
        if self.model_apps.resolution_option:
            for item in self.model_apps.resolution_option:
                self.ui.comboBox_resolution_sources.addItem(f"{str(item[0])} ✕ {str(item[1])}")

    def label_original_mouse_release_event(self, event):
        pass

    def label_original_mouse_move_event(self, event):
        self.model_apps.label_original_mouse_move_event(self.ui.label_image_original, event)

    def label_original_mouse_press_event(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if self.model_apps.state_recent_view == "AnypointView":
                if self.ui.m1Button.isChecked():
                    self.model_apps.label_original_mouse_press_event_anypoint_mode_1(event)
                    self.model_apps.create_maps_anypoint_mode_1()
                    self.anypoint_config.showing_config_mode_1()
                else:
                    self.model_apps.label_original_mouse_press_event_anypoint_mode_2(event)
                    self.model_apps.create_maps_anypoint_mode_2()
                    self.anypoint_config.showing_config_mode_2()

    def label_original_mouse_leave_event(self, _):
        self.model_apps.label_original_mouse_leave_event()

    def label_original_mouse_double_click_event(self, _):
        if self.model_apps.state_recent_view == "AnypointView":
            if self.ui.m1Button.isChecked():
                self.model_apps.label_original_mouse_double_click_anypoint_mode_1()
                self.anypoint_config.showing_config_mode_1()
            else:
                self.model_apps.label_original_mouse_double_click_anypoint_mode_2()
                self.anypoint_config.showing_config_mode_2()

    def update_label_image(self, ui_label: QtWidgets.QLabel, image, width: int = LABEL_IMAGE_WIDTH, scale_content: bool = False):
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)

    # get the slot and signal of the result image (rectilinear) so it can be connected and display it continously
    def setup_result_signal(self, slot: QtCore.pyqtSlot, signal: QtCore.pyqtSignal):
        self.result_slot = slot
        self.result_signal = signal
        self.result_signal.connect(self.result_slot)

    # get the slot and signal of the original image (fisheye) so it can be connected and display it continously
    def setup_original_signal(self, slot: QtCore.pyqtSlot, signal: QtCore.pyqtSignal):
        self.original_slot = slot
        self.original_signal = signal
        self.original_signal.connect(self.original_slot)

    # Escape Key does not invoke closeEvent (to disconnect the signals and slots), so need to do it manually
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        self.reject_function() if (event.key() == QtCore.Qt.Key.Key_Escape) else super().keyPressEvent(event)

    # need to disconnect the signals and slots else RuntimeError: wrapped C/C++ object of type QLabel has been deleted
    # because the QLabel's lifetime will be over when the Setup Dialog is closed but the previous slot and signal will still call it
    def closeEvent(self, event: QtGui.QCloseEvent):
        self.disconnect_signals()
        super().closeEvent(event)

    def reject_function(self):
        if EMPTY_SLOTS == MAX_MONITOR_INDEX:
            self.model_apps.reset_config()
            try: self.model_apps.cap.close()
            except: pass
            self.model_apps.cap = None
        # self.model_apps.deleteLater()
        self.reject()
        self.close()

    def accept_function(self):
        self.accept()
        self.close()

    def disconnect_signals(self):
        self.result_signal.disconnect(self.result_slot)
        self.original_signal.disconnect(self.original_slot)
