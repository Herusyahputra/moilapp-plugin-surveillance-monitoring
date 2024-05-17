from src.plugin_interface import PluginInterface
from src.models.model_apps import Model, ModelApps
from .surveillance import Ui_Form
from .ui_setup import Ui_Setup

from PyQt6 import QtWidgets, QtCore, QtGui
from typing import Any

MAX_MONITOR_INDEX: int = 8
EMPTY_SLOTS: int = 8

class GridManager(object):
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

    def set_slot(self, index: int, element) -> None:
        self.slots[index - 1] = element if (1 <= index <= len(self.slots)) else None

    def clear_slot(self, index: int) -> None:
        self.slots[index - 1] = None if (1 <= index <= len(self.slots)) else self.slots[index - 1]

# for the setup dialog
class SetupDialog(QtWidgets.QDialog):
    def __init__(self, model_apps: ModelApps):
        super().__init__()
        
        self.model: Model = Model()
        self.model_apps: ModelApps = model_apps
        
        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.accept_function)
        self.ui.cancelButton.clicked.connect(self.reject_function)

        # setup and gracefully close the slots and signals of ModelApps (image_result and signal_image_original)
        update_original_label_slot = lambda img: self.update_label_image(self.ui.label_image_original, img)
        update_result_label_slot = lambda img: self.update_label_image(self.ui.label_image_result, img)
        self.setup_original_signal(update_original_label_slot, self.model_apps.signal_image_original)
        self.setup_result_signal(update_result_label_slot, self.model_apps.image_result)

        self.ui.m1Button.setChecked(True)
        self.ui.modeSelectGroup.buttonClicked.connect(self.mode_select_clicked)
        self.mode_select_clicked()
        
        self.ui.label_15.hide()
        self.ui.comboBox_resolution_sources.hide()

        self.ui.checkBox.stateChanged.connect(self.checkbox_click)
        self.ui.checkBox.setChecked(True)
        self.checkbox_click()
        
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
        
        # ui_setup.cancelButton.clicked.connect(dialog.close_functon)
        # self.ui.okButton.clicked.connect(dialog.accept_function)
        
        self.ui.okButton.setText("OK")
                
        # self.ui.alphaSpinbox.valueChanged.connect(self.change_alpha_beta_optical_point)
        # self.ui.betaSpinbox.valueChanged.connect(self.change_alpha_beta_optical_point)
        # self.ui.yawSpinbox.valueChanged.connect()
        # self.ui.pitchSpinbox.valueChanged.connect()
        # self.ui.rollSpinbox.valueChanged.connect()
        # self.ui.zoomSpinbox.valueChanged.connect(control_change_zooming)

        self.model_apps.alpha_beta.connect(self.alpha_beta_from_coordinate)
        self.model_apps.value_coordinate.connect(self.set_value_coordinate)
        self.model_apps.state_rubberband = False

        # setup mouse events
        # ui_setup.label_image_original.mouseReleaseEvent =
        self.ui.label_image_original.mouseMoveEvent = lambda event: self.model_apps.label_original_mouse_move_event(self.ui.label_image_original, event)
        self.ui.label_image_original.mousePressEvent = lambda event: self.model_apps.label_original_mouse_move_event(self.ui.label_image_original, event)
        self.ui.label_image_original.leaveEvent = lambda event: self.model_apps.label_original_mouse_leave_event()
        # ui_setup.label_image_original.mouseDoubleClickEvent =

    def change_alpha_beta_optical_point(self):
        alpha = self.ui.alphaSpinbox.value()
        beta = self.ui.betaSpinbox.value()
        self.model_apps.change_alpha_beta_by_spinbox(alpha, beta)
    
    def set_value_coordinate(self, coordinate):
        self.ui.label_pos_x.setText(str(coordinate[0]))
        self.ui.label_pos_y.setText(str(coordinate[1]))

    # set up Anypoint Mode 1 or 2 with state_recent_view = "AnypointView"
    def mode_select_clicked(self) -> None:
        self.ui.frameMode1.hide()
        self.ui.frameMode2.hide()
        
        if self.ui.m1Button.isChecked():
            self.ui.frameMode1.show()
            self.model_apps.state_recent_view = "AnypointView"
            self.model_apps.change_anypoint_mode = "mode_1"
            self.model_apps.create_maps_anypoint_mode_1()
        else:
            self.ui.frameMode2.show()
            self.model_apps.state_recent_view = "AnypointView"
            self.model_apps.change_anypoint_mode = "mode_2"
            self.model_apps.create_maps_anypoint_mode_2()
    
    def checkbox_click(self) -> None:
        if self.ui.checkBox.isChecked():
            self.model_apps.set_draw_polygon = True
        else:
            self.model_apps.set_draw_polygon = False
        
    def alpha_beta_from_coordinate(self, alpha_beta: list) -> None:
        self.ui.alphaSpinbox.blockSignals(True)
        self.ui.betaSpinbox.blockSignals(True)
        self.ui.alphaSpinbox.setValue(alpha_beta[0])
        self.ui.betaSpinbox.setValue(alpha_beta[1])
        self.ui.alphaSpinbox.blockSignals(False)
        self.ui.betaSpinbox.blockSignals(False)
        self.ui.label_alpha.setText(str(alpha_beta[0]))
        self.ui.label_beta.setText(str(alpha_beta[1]))
        

    def update_label_image(self, ui_label: QtWidgets.QLabel, image: Any, width: int = 300, scale_content: bool = False) -> None:
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)

    # get the slot and signal of the result image (rectilinear) so it can be connected and display it continously
    def setup_result_signal(self, slot: Any, signal: Any) -> None:
        self.result_slot: Any = slot
        self.result_signal: Any = signal
        self.result_signal.connect(self.result_slot)

    # get the slot and signal of the original image (fisheye) so it can be connected and display it continously
    def setup_original_signal(self, slot: Any, signal: Any) -> None:
        self.original_slot: Any = slot
        self.original_signal: Any = signal
        self.original_signal.connect(self.original_slot)

    # Escape Key does not invoke closeEvent (to disconnect the signals and slots), so need to do it manually
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        self.reject_function() if (event.key() == QtCore.Qt.Key.Key_Escape) else super().keyPressEvent(event)

    # need to disconnect the signals and slots else RuntimeError: wrapped C/C++ object of type QLabel has been deleted
    # because the QLabel's lifetime will be over when the Setup Dialog is closed but the previous slot and signal will still call it
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.disconnect_signals()
        del self.model_apps
        super().closeEvent(event)

    def reject_function(self) -> None:
        if EMPTY_SLOTS == MAX_MONITOR_INDEX:
            self.model_apps.reset_config()
            try: self.model_apps.cap.close()
            except: pass
            self.model_apps.cap = None
        self.reject()
        self.close()

    def accept_function(self) -> None:
        self.accept()
        self.close()

    def disconnect_signals(self) -> None:
        self.result_signal.disconnect(self.result_slot)
        self.original_signal.disconnect(self.original_slot)

class Controller(QtWidgets.QWidget):
    def __init__(self, model: Model):
        super().__init__()

        self.model: Model = model

        self.ui: Ui_Form = Ui_Form()
        self.ui.setupUi(self)
        
        self.ui.addButton.clicked.connect(self.add_clicked)
        self.ui.fisheyeButton.clicked.connect(self.fisheye_clicked)
        self.ui.paramButton.clicked.connect(self.parameter_clicked)
        self.ui.recordedButton.clicked.connect(self.recorded_clicked)
        self.ui.capturedButton.clicked.connect(self.captured_clicked)

        self.grid_manager: GridManager = GridManager()

        self.set_stylesheet()

    # find every QPushButton, QLabel, QScrollArea, and Line, this works because this class is a subclass of QWidget
    def set_stylesheet(self) -> None:
        [button.setStyleSheet(self.model.style_pushbutton()) for button in self.findChildren(QtWidgets.QPushButton)]
        [label.setStyleSheet(self.model.style_label()) for label in self.findChildren(QtWidgets.QLabel)]
        [scroll_area.setStyleSheet(self.model.style_scroll_area()) for scroll_area in
        
        self.findChildren(QtWidgets.QScrollArea)]
        self.ui.line.setStyleSheet(self.model.style_line())
        self.ui.line_2.setStyleSheet(self.model.style_line())
        self.ui.line_3.setStyleSheet(self.model.style_line())
    
    def get_monitor_ui_by_idx(self, ui_idx) -> tuple[QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton]:
        label: QtWidgets.QLabel               = getattr(self.ui, f"displayLab{ui_idx}")
        setup_button: QtWidgets.QPushButton   = getattr(self.ui, f"setupButton{ui_idx}")
        capture_button: QtWidgets.QPushButton = getattr(self.ui, f"captureButton{ui_idx}")
        delete_button: QtWidgets.QPushButton  = getattr(self.ui, f"deleteButton{ui_idx}")
        return (label, setup_button, capture_button, delete_button)

    def add_clicked(self):
        global EMPTY_SLOTS
        
        ui_idx: int = self.grid_manager.get_empty_slots()[0]
        label, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)

        # I have no idea how this works but I think the order of calling these is important
        # model_apps.create_moildev()
        # model_apps.create_image_original()
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
            model_apps.create_image_result()

            setup_button.clicked.connect(lambda: self.setup_clicked(ui_idx, (source_type, cam_type, media_source, params_name)))
            delete_button.clicked.connect(lambda: self.delete_monitor(model_apps))

            self.grid_manager.set_slot(ui_idx, model_apps)
        
        EMPTY_SLOTS -= 1

    def setup_clicked(self, ui_idx: int, media_sources: tuple) -> None:
        label, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        prev_model_apps: list | None = self.grid_manager.get_slot_by_index(ui_idx)
        model_apps: ModelApps = ModelApps()
        model_apps.update_file_config()
        model_apps.set_media_source(*media_sources)

        return_status: bool | None = self.setup_monitor(model_apps)
        if return_status is False:
            del model_apps
            return

        self.delete_monitor(prev_model_apps)
        model_apps.image_result.connect(lambda img: self.update_label_image(label, img))
        model_apps.create_image_result()
        setup_button.clicked.connect(lambda: self.setup_clicked(ui_idx, media_sources))
        delete_button.clicked.connect(lambda: self.delete_monitor(model_apps))
        self.grid_manager.set_slot(ui_idx, model_apps)
        del prev_model_apps

    def update_label_image(self, ui_label: Ui_Form, image: Any, width: int = 300, scale_content: bool = False):
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)

    def setup_monitor(self, model_apps: ModelApps) -> True:
        dialog: SetupDialog = SetupDialog(model_apps)
        
        # start setup dialog
        result: int = dialog.exec()
        del dialog
        return True if (result == QtWidgets.QDialog.DialogCode.Accepted) else False

    def delete_monitor(self, model_apps: ModelApps) -> None:
        global EMPTY_SLOTS
        
        model_apps: ModelApps = model_apps
        ui_idx: int = self.grid_manager.get_index_of_slot(model_apps)
        
        if ui_idx == -1: return
        
        label, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        label.clear(); label.setText("")
        setup_button.clicked.disconnect()
        # capture_button.clicked.disconnect()
        # delete_button.clicked.disconnect()

        if model_apps.cap is not None:
            model_apps.timer.stop()
            # model_apps.__image_result = None
            model_apps.__image_original = None
            model_apps.image = None
            model_apps.image_resize = None
            
            model_apps.reset_config()
            if model_apps.cap is not None and (len(self.grid_manager.get_empty_slots()) == (MAX_MONITOR_INDEX - 1)):
                try: model_apps.cap.close()
                except: pass
                model_apps.cap = None

        # THIS WILL MAKE "QThread: Destroyed while thread is still running"
        # Already used QTimer.singleShot(1000, lambda: ...) but still same results
        self.grid_manager.clear_slot(ui_idx)
        EMPTY_SLOTS += 1

    def alpha_beta_from_coordinate(self, alpha_beta: Any) -> None:
        print(alpha_beta)

    def captured_clicked(self) -> None:
        pass

    def parameter_clicked(self) -> None:
        self.model.form_camera_parameter()

    def fisheye_clicked(self) -> None:
        print("INFO: \"fisheye_clicked(self)\" function is STILL under development!")

    def recorded_clicked(self) -> None:
        print("INFO: \"recorded_clicked(self)\" function is STILL under development!")

class Surveillance(PluginInterface):
    def __init__(self):
        super().__init__()
        self.widget: None | Any = None
        self.description: str = "Moilapp Plugin: Surveillance monitoring area using Fisheye Camera for a wide 360deg view"

    def set_plugin_widget(self, model) -> Controller:
        self.widget: Controller = Controller(model)
        return self.widget

    def set_icon_apps(self) -> str: return "icon.png"
    def change_stylesheet(self) -> None: self.widget.set_stylesheet()