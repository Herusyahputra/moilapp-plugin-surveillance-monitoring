from src.plugin_interface import PluginInterface
from src.models.model_apps import Model, ModelApps
from .ui_recoder import Ui_Recorder
from .custom_screen_capture import ScreenRecorder
from .ui_surveillance import Ui_Main
from .constants import *
from .control_setup import SetupDialog

from PyQt6 import QtWidgets, QtCore, QtGui


class Controller(QtWidgets.QWidget):
    def __init__(self, model: Model):
        super().__init__()

        self.model: Model = model

        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        self.ui.addButton.clicked.connect(self.add_clicked)
        self.ui.fisheyeButton.clicked.connect(self.fisheye_clicked)
        self.ui.paramButton.clicked.connect(self.parameter_clicked)
        self.ui.capturedButton.clicked.connect(self.captured_clicked)
        self.ui.recordMonitorButton.setStyleSheet(self.model.style_pushbutton_play_pause_video())

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
    
    def get_monitor_ui_by_idx(self, ui_idx) -> tuple[QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton]:
        label: QtWidgets.QLabel               = getattr(self.ui, f"displayLab{ui_idx}")
        label_recording: QtWidgets.QLabel     = getattr(self.ui_recoder, f"displayLab{ui_idx}")
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
            print(source_type, cam_type, media_source, params_name)
            model_apps.set_media_source(source_type, cam_type, media_source, params_name)

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
        
        ui_idx = self.grid_manager.get_index_of_slot(model_apps)
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

class SurveillanceMonitor(PluginInterface):
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