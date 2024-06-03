from src.plugin_interface import PluginInterface
from src.models.model_apps import Model, ModelApps
from .custom_screen_capture import ScreenRecorder
from .constants import *
from .control_setup import SetupDialog
from .views.ui_recoder import Ui_Recorder
from .views.ui_surveillance import Ui_Main
from .views.ui_monitor import Ui_Monitor

from PyQt6 import QtWidgets, QtCore, QtGui


class CustomStackedWidget(QtWidgets.QWidget):
    def __init__(self, widgets, rows=1, columns=1):
        super().__init__()
        self.monitor = widgets
        self.rows = rows
        self.columns = columns
        self.initUI()

    def initUI(self):
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.currentIndex = 0

        # Add widgets to the QStackedWidget

        # Create navigation buttons
        self.prevButton = QtWidgets.QPushButton("Previous")
        self.nextButton = QtWidgets.QPushButton("Next")
        self.prevButton.clicked.connect(self.showPrevious)
        self.nextButton.clicked.connect(self.showNext)

        self.updateStackedWidget()

        # Layout for navigation buttons
        navLayout = QtWidgets.QHBoxLayout()
        navLayout.addWidget(self.prevButton)
        navLayout.addWidget(self.nextButton)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(navLayout)
        mainLayout.addWidget(self.stackedWidget)

        self.setLayout(mainLayout)
        self.updateButtons()

    def updateStackedWidget(self):
        # Clear existing widgets from the QStackedWidget
        while self.stackedWidget.count() > 0:
            widget = self.stackedWidget.widget(0)
            self.stackedWidget.removeWidget(widget)
            widget.deleteLater()
        # Add widgets with the new grid size
        for i in range(0, len(self.monitor), self.rows * self.columns):
            page = QtWidgets.QWidget()
            pageLayout = QtWidgets.QGridLayout(page)
            for j in range(self.rows * self.columns):
                row, col = divmod(j, self.columns)
                if i + j < len(self.monitor):
                    pageLayout.addWidget(self.monitor[i + j], row, col)
            page.setLayout(pageLayout)
            self.stackedWidget.addWidget(page)
        if self.rows * self.columns == len(self.monitor):
            self.nextButton.hide()
            self.prevButton.hide()
        else:
            self.nextButton.show()
            self.prevButton.show()

    def showPrevious(self):
        self.currentIndex -= 1
        if self.currentIndex < 0:
            self.currentIndex = self.stackedWidget.count() - 1
        self.stackedWidget.setCurrentIndex(self.currentIndex)
        self.updateButtons()

    def showNext(self):
        self.currentIndex += 1
        if self.currentIndex >= self.stackedWidget.count():
            self.currentIndex = 0
        self.stackedWidget.setCurrentIndex(self.currentIndex)
        self.updateButtons()

    def updateButtons(self):
        self.prevButton.setEnabled(self.stackedWidget.count() > 1)
        self.nextButton.setEnabled(self.stackedWidget.count() > 1)

    def setGridSize(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.updateStackedWidget()
        self.updateButtons()
        
class CustomWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.enable_filter = True
        self.menuFrame = None

        self.setMinimumSize(QtCore.QSize(340, 260))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)

    def eventFilter(self, obj, event):
        if obj == self and self.enable_filter and self.menuFrame:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.menuFrame.show()
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.menuFrame.hide()
        return super().eventFilter(obj, event)

class Controller(QtWidgets.QWidget):
    def __init__(self, model: Model):
        super().__init__()

        self.model = model

        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        self.ui.addButton.clicked.connect(self.add_clicked)
        self.ui.fisheyeButton.clicked.connect(self.fisheye_clicked)
        self.ui.paramButton.clicked.connect(self.parameter_clicked)
        self.ui.galleryButton.clicked.connect(self.gallery_clicked)
        self.ui.recordMonitorButton.setStyleSheet(self.model.style_pushbutton_play_pause_video())

        widgets = []
        for i in range(8):
            widget = CustomWidget()
            ui_monitor = Ui_Monitor()
            ui_monitor.setupUi(widget)
            
            widget.menuFrame = ui_monitor.menuFrame 
            widget.displayLab = ui_monitor.displayLab
            widget.captureButton = ui_monitor.captureButton
            widget.setupButton = ui_monitor.setupButton
            widget.deleteButton = ui_monitor.deleteButton
            widget.menuFrame.hide()
            
            widgets.append(widget)
    
        self.grid_monitor = CustomStackedWidget(widgets, 2, 4)
        self.ui.stackedWidget.addWidget(self.grid_monitor)
        self.ui.layoutOneByOneButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutOneByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByFourButton.clicked.connect(self.relayout_grid_clicked)
        self.model_apps_manager = ModelAppsManager()

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
        [scroll_area.setStyleSheet(self.model.style_scroll_area()) for scroll_area in self.findChildren(QtWidgets.QScrollArea)]
        
        self.ui.line.setStyleSheet(self.model.style_line())
        self.ui.line_2.setStyleSheet(self.model.style_line())
        self.ui.line_3.setStyleSheet(self.model.style_line())
    
    def get_monitor_ui_by_idx(self, ui_idx) -> tuple[QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton]:
        label_recording: QtWidgets.QLabel     = getattr(self.ui_recoder, f"displayLab{ui_idx + 1}")
    
        label: QtWidgets.QLabel               = self.grid_monitor.monitor[ui_idx].displayLab
        setup_button: QtWidgets.QPushButton   = self.grid_monitor.monitor[ui_idx].setupButton
        capture_button: QtWidgets.QPushButton = self.grid_monitor.monitor[ui_idx].captureButton
        delete_button: QtWidgets.QPushButton  = self.grid_monitor.monitor[ui_idx].deleteButton
    
        return (label, label_recording, setup_button, capture_button, delete_button)

    def start_stop_recording(self):
        if self.ui.recordMonitorButton.isChecked():
            self.recorder.start()
        else:
            self.recorder.stop()
            self.recorder.save_video()

    def add_clicked(self):
        global EMPTY_SLOTS
        
        ui_idx: int = self.model_apps_manager.get_empty_slots()
        if ui_idx:
            ui_idx = ui_idx[0]
            label, label_recording, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setStyleSheet("font-family: Segoe UI; font-size:14px;")
            msg.setWindowTitle("Information!")
        
            msg.setText("Cannot add more monitors!")
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()
            return

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

            self.model_apps_manager.set_slot(ui_idx, model_apps)
        
        EMPTY_SLOTS -= 1

    def setup_clicked(self, ui_idx: int, media_sources: tuple):
        label, label_recording, setup_button, capture_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        prev_model_apps: list = self.model_apps_manager.get_slot_by_index(ui_idx)
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
        self.model_apps_manager.set_slot(ui_idx, model_apps)
        del prev_model_apps

    def update_label_image(self, ui_label, image, width: int = 340, scale_content: bool = False):
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)

    def setup_monitor(self, model_apps: ModelApps) -> bool:
        dialog: SetupDialog = SetupDialog(model_apps)
        
        result: int = dialog.exec()
        del dialog
        return True if (result == QtWidgets.QDialog.DialogCode.Accepted) else False

    def delete_monitor(self, model_apps: ModelApps):
        global EMPTY_SLOTS
        
        ui_idx = self.model_apps_manager.get_index_of_slot(model_apps)
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
            if model_apps.cap is not None and (len(self.model_apps_manager.get_empty_slots()) == (MAX_MONITOR_INDEX - 1)):
                try: model_apps.cap.close()
                except: pass
                model_apps.cap = None

        self.model_apps_manager.clear_slot(ui_idx)
        EMPTY_SLOTS += 1

    def gallery_clicked(self):
        print("INFO: \"gallery_clicked()\" function is STILL under development!")

    def parameter_clicked(self):
        self.model.form_camera_parameter()

    def fisheye_clicked(self):
        print("INFO: \"fisheye_clicked()\" function is STILL under development!")
        
    
    def relayout_grid_clicked(self):
        if self.sender().objectName() == 'layoutOneByOneButton':
            self.grid_monitor.setGridSize(1, 1)
        elif self.sender().objectName() == 'layoutOneByTwoButton':
            self.grid_monitor.setGridSize(1, 2)
        elif self.sender().objectName() == 'layoutTwoByTwoButton':
            self.grid_monitor.setGridSize(2, 2)
        elif self.sender().objectName() == 'layoutTwoByFourButton':
            self.grid_monitor.setGridSize(2, 4)
        

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