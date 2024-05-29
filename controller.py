from src.plugin_interface import PluginInterface
from src.models.model_apps import Model, ModelApps
from src.controllers.control_anypoint import AnypointConfig
from .ui_recoder import Ui_Recorder
from .custom_screen_capture import ScreenRecorder
from .ui_surveillance import Ui_Main
from .ui_setup import Ui_Setup

from PyQt6 import QtWidgets, QtCore, QtGui

MAX_MONITOR_INDEX: int = 8
EMPTY_SLOTS: int = 8

class GridManager:
    def __init__(self):
        self.slots = [None] * 8

    def get_index_of_slot(self, element) -> int:
        try:
            index: int = self.slots.index(element)
            return (index + 1)
        except ValueError:
            return -1

    def get_slot_by_index(self, index: int):
        return self.slots[index - 1] if (1 <= index <= len(self.slots)) else None

    def get_empty_slots(self) -> list:
        return [i + 1 for i, slot in enumerate(self.slots) if slot is None]

    def get_used_slots(self) -> list:
        return [i + 1 for i, slot in enumerate(self.slots) if slot is not None]

    def set_slot(self, index: int, element):
        self.slots[index - 1] = element if (1 <= index <= len(self.slots)) else None

    def clear_slot(self, index: int):
        self.slots[index - 1] = None if (1 <= index <= len(self.slots)) else self.slots[index - 1]

# for the setup dialog
class SetupDialog(QtWidgets.QDialog):
    def __init__(self, model_apps: ModelApps):
        super().__init__()
        
        
        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.accept_function)
        self.ui.cancelButton.clicked.connect(self.reject_function)
        
        self.model: Model = Model()
        self.model_apps: ModelApps = model_apps
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
        self.ui.label_image_original.mousePressEvent = self.label_original_mouse_press_event
        self.ui.label_image_original.leaveEvent = self.label_original_mouse_leave_event
        self.ui.label_image_original.mouseDoubleClickEvent = self.label_original_mouse_double_click_event

        self.ui.doubleSpinBox_alpha.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_beta.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_roll.valueChanged.connect(self.change_properties_anypoint)
        self.ui.doubleSpinBox_zoom.valueChanged.connect(self.change_properties_anypoint)

        self.set_stylesheet()

    def set_stylesheet(self):
        self.ui.label_title_original.setStyleSheet(self.model.style_label())
        self.ui.label_title_image_result.setStyleSheet(self.model.style_label())
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
    
    def set_value_coordinate(self, coordinate):
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
        if self.ui.checkBox.isChecked():
            self.model_apps.set_draw_polygon = True
        else:
            self.model_apps.set_draw_polygon = False
        
    def alpha_beta_from_coordinate(self, alpha_beta: list):
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

        self.ui.label_alpha.setText(str(round(alpha_beta[0], 2)))
        self.ui.label_beta.setText(str(round(alpha_beta[1], 2)))

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
                self.ui.comboBox_resolution_sources.addItem(f"{str(item[0])} x {str(item[1])}")


    def label_original_mouse_release_event(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pass
        else:
            self.menu_mouse_event(event, "label_original")

    def label_original_mouse_move_event(self, event):
        self.model_apps.label_original_mouse_move_event(self.ui.label_image_original, event)

    def label_original_mouse_press_event(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if self.model_apps.state_rubberband:
                print("under developing")
            else:
                if self.model_apps.state_recent_view == "AnypointView":
                    if self.ui.m1Button.isChecked():
                        self.model_apps.label_original_mouse_press_event_anypoint_mode_1(event)
                        self.model_apps.create_maps_anypoint_mode_1()
                        self.anypoint_config.showing_config_mode_1()
                    else:
                        self.model_apps.label_original_mouse_press_event_anypoint_mode_2(event)
                        self.model_apps.create_maps_anypoint_mode_2()
                        self.anypoint_config.showing_config_mode_2()

    def label_original_mouse_leave_event(self, event):
        self.model_apps.label_original_mouse_leave_event()

    def label_original_mouse_double_click_event(self, event):
        if self.model_apps.state_recent_view == "AnypointView":
            if self.ui.m1Button.isChecked():
                self.model_apps.label_original_mouse_double_click_anypoint_mode_1()
                self.anypoint_config.showing_config_mode_1()
            else:
                self.model_apps.label_original_mouse_double_click_anypoint_mode_2()
                self.anypoint_config.showing_config_mode_2()

    def update_label_image(self, ui_label: QtWidgets.QLabel, image, width: int = 300, scale_content: bool = False):
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
        del self.model_apps
        super().closeEvent(event)

    def reject_function(self):
        if EMPTY_SLOTS == MAX_MONITOR_INDEX:
            self.model_apps.reset_config()
            try: self.model_apps.cap.close()
            except: pass
            self.model_apps.cap = None
        self.reject()
        self.close()

    def accept_function(self):
        self.accept()
        self.close()

    def disconnect_signals(self):
        self.result_signal.disconnect(self.result_slot)
        self.original_signal.disconnect(self.original_slot)

class Controller(QtWidgets.QWidget):
    def __init__(self, model: Model):
        super().__init__()

        self.model: Model = model

        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        self.ui.addButton.clicked.connect(self.add_clicked)
        self.ui.fisheyeButton.clicked.connect(self.fisheye_clicked)
        self.ui.paramButton.clicked.connect(self.parameter_clicked)
        self.ui.recordedButton.clicked.connect(self.recorded_clicked)
        self.ui.capturedButton.clicked.connect(self.captured_clicked)

        self.grid_manager: GridManager = GridManager()

        self.set_stylesheet()

        self.ui_recoder = Ui_Recorder()
        self.recoder_widget = QtWidgets.QWidget()
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.recoder_widget.setMinimumSize(screen_width, screen_height)
        self.recoder_widget.setMaximumSize(screen_width, screen_height)
        self.recoder_widget.showMaximized()
        self.recoder_widget.hide()
        self.ui_recoder.setupUi(self.recoder_widget)
        self.recorder = ScreenRecorder(self.recoder_widget)

        self.ui.recordMonitorButton.clicked.connect(self.start_stop_recording)

    # find every QPushButton, QLabel, QScrollArea, and Line, this works because this class is a subclass of QWidget
    def set_stylesheet(self):
        [button.setStyleSheet(self.model.style_pushbutton()) for button in self.findChildren(QtWidgets.QPushButton)]
        [label.setStyleSheet(self.model.style_label()) for label in self.findChildren(QtWidgets.QLabel)]
        [scroll_area.setStyleSheet(self.model.style_scroll_area()) for scroll_area in
        
        self.findChildren(QtWidgets.QScrollArea)]
        self.ui.line.setStyleSheet(self.model.style_line())
        self.ui.line_2.setStyleSheet(self.model.style_line())
        self.ui.line_3.setStyleSheet(self.model.style_line())

        self.ui.recordMonitorButton.setStyleSheet(self.model.style_pushbutton_play_pause_video())
    
    def get_monitor_ui_by_idx(self, ui_idx) -> tuple[QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton]:
        label: QtWidgets.QLabel               = getattr(self.ui, f"displayLab{ui_idx}")
        label_recording: QtWidgets.QLabel               = getattr(self.ui_recoder, f"displayLab{ui_idx}")
        setup_button: QtWidgets.QPushButton   = getattr(self.ui, f"setupButton{ui_idx}")
        capture_button: QtWidgets.QPushButton = getattr(self.ui, f"captureButton{ui_idx}")
        delete_button: QtWidgets.QPushButton  = getattr(self.ui, f"deleteButton{ui_idx}")
        return (label, label_recording, setup_button, capture_button, delete_button)

    def start_stop_recording(self):
        if self.ui.recordMonitorButton.isChecked():
            self.recorder.start()
        else:
            self.recorder.stop()
            self.recorder.save_video()

    def add_clicked(self):
        global EMPTY_SLOTS
        
        ui_idx: int = self.grid_manager.get_empty_slots()[0]
        label, label_recording, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)

        source_type, cam_type, media_source, params_name = self.model.select_media_source()
        if media_source is not None:
            model_apps: ModelApps = ModelApps()
            model_apps.update_file_config()
            model_apps.set_media_source(source_type, cam_type, media_source, params_name)
            model_apps.create_maps_fov()

            return_status = self.setup_monitor(model_apps)
            if return_status is False:
                del model_apps
                return

            model_apps.image_result.connect(lambda img: self.update_label_image(label, img))
            model_apps.image_result.connect(lambda img: self.update_label_image(label_recording, img))
            model_apps.create_image_result()

            setup_button.clicked.connect(lambda: self.setup_clicked(ui_idx, (source_type, cam_type, media_source, params_name)))
            delete_button.clicked.connect(lambda: self.delete_monitor(model_apps))

            self.grid_manager.set_slot(ui_idx, model_apps)
        
        EMPTY_SLOTS -= 1

    def setup_clicked(self, ui_idx: int, media_sources: tuple):
        label, label_recording, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        prev_model_apps: list = self.grid_manager.get_slot_by_index(ui_idx)
        model_apps: ModelApps = ModelApps()
        model_apps.update_file_config()
        model_apps.set_media_source(*media_sources)

        return_status: bool = self.setup_monitor(model_apps)
        if return_status is False:
            del model_apps
            return

        self.delete_monitor(prev_model_apps)
        model_apps.image_result.connect(lambda img: self.update_label_image(label, img))
        model_apps.image_result.connect(lambda img: self.update_label_image(label_recording, img))
        model_apps.create_image_result()
        setup_button.clicked.connect(lambda: self.setup_clicked(ui_idx, media_sources))
        delete_button.clicked.connect(lambda: self.delete_monitor(model_apps))
        self.grid_manager.set_slot(ui_idx, model_apps)
        del prev_model_apps

    def update_label_image(self, ui_label, image, width: int = 300, scale_content: bool = False):
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)

    def setup_monitor(self, model_apps: ModelApps) -> bool:
        dialog: SetupDialog = SetupDialog(model_apps)
        
        result: int = dialog.exec()
        del dialog
        return True if (result == QtWidgets.QDialog.DialogCode.Accepted) else False

    def delete_monitor(self, model_apps: ModelApps):
        global EMPTY_SLOTS
        
        model_apps: ModelApps = model_apps
        ui_idx: int = self.grid_manager.get_index_of_slot(model_apps)
        
        if ui_idx == -1: return
        
        label, label_recording, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        label.clear()
        label.setText("")
        label_recording.clear()
        label_recording.setText("")
        setup_button.clicked.disconnect()
        # capture_button.clicked.disconnect()
        delete_button.clicked.disconnect()

        if model_apps.cap is not None:
            model_apps.timer.stop()
            model_apps.__image_original = None
            model_apps.image = None
            model_apps.image_resize = None
            
            model_apps.reset_config()
            if model_apps.cap is not None and (len(self.grid_manager.get_empty_slots()) == (MAX_MONITOR_INDEX - 1)):
                try: model_apps.cap.close()
                except: pass
                model_apps.cap = None

        self.grid_manager.clear_slot(ui_idx)
        EMPTY_SLOTS += 1

    def captured_clicked(self):
        pass

    def parameter_clicked(self):
        self.model.form_camera_parameter()

    def fisheye_clicked(self):
        print("INFO: \"fisheye_clicked()\" function is STILL under development!")

    def recorded_clicked(self):
        print("INFO: \"recorded_clicked()\" function is STILL under development!")

class Surveillance(PluginInterface):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.description = "Moilapp Plugin: Surveillance monitoring area using Fisheye Camera for a wide 360deg view"

    def set_plugin_widget(self, model):
        self.widget = Controller(model)
        return self.widget

    def set_icon_apps(self): 
        return "icon.png"
    
    def change_stylesheet(self): 
        self.widget.set_stylesheet()