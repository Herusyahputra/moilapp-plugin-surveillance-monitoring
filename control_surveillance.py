from src.plugin_interface import PluginInterface
from src.models.model_apps import Model, ModelApps
from .custom_screen_capture import ScreenRecorder
from .constants import *
from .control_setup import SetupDialog
from .views.recorder_ui import Ui_Recorder
from .views.surveillance_ui import Ui_Main
from .views.monitor_ui import Ui_Monitor

from PyQt6 import QtWidgets, QtCore, QtGui
import os.path as osp

class CustomStackedWidget(QtWidgets.QWidget):
    def __init__(self, widgets, rows=1, columns=1):
        super().__init__()
        self.monitors = widgets
        self.rows = rows
        self.columns = columns
        self.initUI()

    def initUI(self):
        self.stackedPages = QtWidgets.QStackedWidget()
        self.currentIndex = 0

        # Create navigation buttons
        self.prevButton = QtWidgets.QPushButton("🔙 Go to PREVIOUS")
        self.nextButton = QtWidgets.QPushButton("🔜 Go to NEXT")
        self.prevButton.clicked.connect(self.showPrevious)
        self.nextButton.clicked.connect(self.showNext)

        # Add widgets to the QStackedWidget
        self.updateStackedWidget()

        # Layout for navigation buttons
        navLayout = QtWidgets.QHBoxLayout()
        navLayout.addWidget(self.prevButton)
        navLayout.addWidget(self.nextButton)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(navLayout)
        mainLayout.addWidget(self.stackedPages)

        self.setLayout(mainLayout)
        self.updateButtons()

    def updateStackedWidget(self):
        # Clear existing widgets from the QStackedWidget
        while self.stackedPages.count() > 0:
            widget = self.stackedPages.widget(0)
            self.stackedPages.removeWidget(widget)
            widget.deleteLater()
            
        # Add widgets with the new grid size
        for i in range(0, len(self.monitors), self.rows * self.columns):
            page = QtWidgets.QWidget()
            pageLayout = QtWidgets.QGridLayout(page)
            for j in range(self.rows * self.columns):
                row, col = divmod(j, self.columns)
                if i + j < len(self.monitors):
                    pageLayout.addWidget(self.monitors[i + j], row, col)
                    self.monitors[i + j].cur_index = str(i + j)
            page.setLayout(pageLayout)
            self.stackedPages.addWidget(page)
        
        if self.rows * self.columns == len(self.monitors):
            self.nextButton.hide()
            self.prevButton.hide()
        else:
            self.nextButton.show()
            self.prevButton.show()

    def showPrevious(self):
        self.currentIndex -= 1
        if self.currentIndex < 0:
            self.currentIndex = self.stackedPages.count() - 1
        self.stackedPages.setCurrentIndex(self.currentIndex)
        self.updateButtons()

    def showNext(self):
        self.currentIndex += 1
        if self.currentIndex >= self.stackedPages.count():
            self.currentIndex = 0
        self.stackedPages.setCurrentIndex(self.currentIndex)
        self.updateButtons()

    def updateButtons(self):
        self.prevButton.setEnabled(self.stackedPages.count() > 1)
        self.nextButton.setEnabled(self.stackedPages.count() > 1)

    def setGridSize(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.updateStackedWidget()
        self.updateButtons()
        
class CustomWidget(QtWidgets.QWidget):
    swap_signal = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.enable_hover = False
        self.enable_drag_drop = False
        self.menuFrame = None
        self.scrollArea = None
        self.cur_index = '0'

        self.setMinimumSize(QtCore.QSize(LABEL_IMAGE_WIDTH, LABEL_IMAGE_HEIGHT))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.setAcceptDrops(True)
    
    def get_width(self) -> int:
        if self.scrollArea:
            w = self.scrollArea.width()
            if w is not None: return w

    def eventFilter(self, obj, event):
        if obj == self and self.enable_hover and self.menuFrame:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.menuFrame.show()
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.menuFrame.hide()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.enable_drag_drop:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setText(self.cur_index)
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint() - self.rect().topLeft())

            self.hide()
            drag.exec(QtCore.Qt.DropAction.MoveAction)
            self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        global MAX_MONITOR_INDEX, EMPTY_SLOTS, LATEST_MOVED_WIDGET, MONITORS_POSITIONS
        
        id = 0
        updated_ui_idx = {}
        if event.mimeData().hasText():
            sender = event.mimeData().text()
            receiver = self.cur_index
            self.swap_signal.emit(sender, receiver)
            
            for i in range(MAX_MONITOR_INDEX):
                try:
                    if int(LATEST_MOVED_WIDGET[i]["PREV"]) == int(sender) and int(LATEST_MOVED_WIDGET[i]["NEXT"]) != int(receiver) and AVAILABLE_MONITORS[int(receiver)] != 1:
                        pass
                        
                    updated_ui_idx = {"ID": int(MONITORS_POSITIONS[int(sender)]), "PREV": int(sender) + 1, "NEXT": int(receiver) + 1}
                    LATEST_MOVED_WIDGET[int(sender)], LATEST_MOVED_WIDGET[int(receiver)] = None, updated_ui_idx
                    AVAILABLE_MONITORS[int(sender)], AVAILABLE_MONITORS[int(receiver)] = 0, 1
                    break
                    
                except TypeError: pass
                except KeyError: pass
            
            MONITORS_POSITIONS[int(sender)], MONITORS_POSITIONS[int(receiver)] = MONITORS_POSITIONS[int(receiver)], MONITORS_POSITIONS[int(sender)]
        
        print(LATEST_MOVED_WIDGET)
        print(AVAILABLE_MONITORS)
        print(MONITORS_POSITIONS)

class Controller(QtWidgets.QWidget):
    def __init__(self, model: Model):
        global MAX_MONITOR_INDEX
        
        super().__init__()

        self.model = model
        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        self.ui.addButton.clicked.connect(self.add_clicked)
        self.ui.fisheyeButton.clicked.connect(self.original_view_clicked)
        self.ui.paramButton.clicked.connect(self.parameter_clicked)
        self.ui.galleryButton.clicked.connect(self.gallery_clicked)

        widgets = []
        for i in range(MAX_MONITOR_INDEX * 2):
            widget = CustomWidget()
            ui_monitor = Ui_Monitor()
            ui_monitor.setupUi(widget)
            ui_monitor.menuFrame.hide()
            ui_monitor.displayLab.setScaledContents(True)
            
            if i < MAX_MONITOR_INDEX:
                widget.enable_drag_drop = True
                widget.enable_hover = True
                widget.menuFrame = ui_monitor.menuFrame 
                widget.setupButton = ui_monitor.setupButton
                widget.captureButton = ui_monitor.captureButton
                widget.duplicateButton = ui_monitor.duplicateButton
                widget.deleteButton = ui_monitor.deleteButton
            widget.displayLab = ui_monitor.displayLab
            widget.scrollArea = ui_monitor.scrollArea
            widgets.append(widget)
        
        self.image_width = LABEL_IMAGE_WIDTH
    
        self.grid_monitor = CustomStackedWidget(widgets[:8], 2, 4)
        self.grid_original_monitor = CustomStackedWidget(widgets[8:], 2, 4)
        self.ui.stackedWidget.addWidget(self.grid_monitor)
        self.ui.stackedWidget.addWidget(self.grid_original_monitor)
        self.ui.layoutOneByOneButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutOneByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByFourButton.clicked.connect(self.relayout_grid_clicked)
        self.model_apps_manager = ModelAppsManager()

        recorder_widgets = []
        for i in range(MAX_MONITOR_INDEX):
            widget = CustomWidget()
            ui_monitor = Ui_Monitor()
            ui_monitor.setupUi(widget)
            ui_monitor.menuFrame.hide()
            ui_monitor.displayLab.setScaledContents(True)
            widget.displayLab = ui_monitor.displayLab
            widget.scrollArea = ui_monitor.scrollArea
            recorder_widgets.append(widget)
            
        self.recorder_widget = CustomStackedWidget(recorder_widgets, 2, 4)
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.recorder_widget.setMinimumSize(screen_width, screen_height)
        self.recorder_widget.setMaximumSize(screen_width, screen_height)
        self.recorder_widget.showMaximized()
        self.recorded_image_width = round((screen_width // 4) / 20) * 20
        self.recorder_widget.hide()
        self.recorder = ScreenRecorder(self.recorder_widget)
        self.ui.recordMonitorButton.clicked.connect(self.start_stop_recording)
        [monitor.swap_signal.connect(self.handle_swapping) for monitor in self.grid_monitor.monitors]
        self.tmp_model_apps_container = []
        self.image_results = {}
        self.set_stylesheet()
        
    def style_monitor_label(self):
        if self.model.theme == "light":
            stylesheet = """
                            QLabel { 
                                background-color: rgb(200,205,205);
                                border-radius: 3px;
                                font-family: Segoe UI;
                                font-size: 24px;
                            }
                            """
        else:
            stylesheet = """
                            QLabel { 
                                background-color: #17202b;
                                border-radius: 3px;
                                font-family: Segoe UI;
                                font-size: 24px;
                            }
                        """
        return stylesheet

    # find every QPushButton, QLabel, QScrollArea, and Line, this works because this class is a subclass of QWidget
    def set_stylesheet(self):
        global MAX_MONITOR_INDEX
        
        [button.setStyleSheet(self.model.style_pushbutton()) for button in self.findChildren(QtWidgets.QPushButton)]
        [scroll_area.setStyleSheet(self.model.style_scroll_area()) for scroll_area in self.findChildren(QtWidgets.QScrollArea)]
        
        [label.setStyleSheet(self.style_monitor_label()) for label in self.findChildren(QtWidgets.QLabel)]
        [label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter) for label in self.findChildren(QtWidgets.QLabel)]
        [label.setText(f"{monitor_id - MAX_MONITOR_INDEX}" if monitor_id - MAX_MONITOR_INDEX > 0 else f"{monitor_id + 1}") for monitor_id, label in enumerate(self.findChildren(QtWidgets.QLabel))]
        
        self.ui.line.setStyleSheet(self.model.style_line())
        self.ui.line_2.setStyleSheet(self.model.style_line())
        self.ui.line_3.setStyleSheet(self.model.style_line())
        self.ui.recordMonitorButton.setStyleSheet(self.model.style_pushbutton_play_pause_video())
        self.recorder_widget.setStyleSheet('background-color: black;')
        [label.setStyleSheet('background-color: black;') for label in self.recorder_widget.findChildren(QtWidgets.QLabel)]
    
    def get_monitor_ui_by_idx(self, ui_idx) -> tuple[QtWidgets.QLabel, QtWidgets.QLabel, QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton, QtWidgets.QPushButton]:
        label_recording: QtWidgets.QLabel     = self.recorder_widget.monitors[ui_idx].displayLab
        label: QtWidgets.QLabel               = self.grid_monitor.monitors[ui_idx].displayLab
        setup_button: QtWidgets.QPushButton   = self.grid_monitor.monitors[ui_idx].setupButton
        capture_button: QtWidgets.QPushButton = self.grid_monitor.monitors[ui_idx].captureButton
        duplicate_button: QtWidgets.QPushButton = self.grid_monitor.monitors[ui_idx].duplicateButton
        delete_button: QtWidgets.QPushButton  = self.grid_monitor.monitors[ui_idx].deleteButton
        label_original: QtWidgets.QLabel      = self.grid_original_monitor.monitors[ui_idx].displayLab
        
        return (label, label_original, label_recording, setup_button, capture_button, duplicate_button, delete_button)

    def start_stop_recording(self):
        if self.ui.recordMonitorButton.isChecked():
            self.recorder.start()
        else:
            self.recorder.stop()
            self.recorder.save_video()

    def add_clicked(self):
        global LATEST_MOVED_WIDGET, AVAILABLE_MONITORS, EMPTY_SLOTS
        
        ui_idx = self.model_apps_manager.get_empty_model_apps()
        if not ui_idx:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setStyleSheet("font-family: Segoe UI; font-size:14px;")
            msg.setWindowTitle("Information!")
        
            msg.setText("Cannot add more monitors!")
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        
        ui_idx: int = ui_idx[0]
        media_sources = self.model.select_media_source()
        self.connect_monitor(ui_idx, media_sources)
        
        LATEST_MOVED_WIDGET[ui_idx] = {"ID": ui_idx, "PREV": ui_idx, "NEXT": ui_idx}
        AVAILABLE_MONITORS[ui_idx] = ui_idx
        EMPTY_SLOTS -= 1
        
    def setup_clicked(self, media_sources: tuple):
        ui_idx = self.grid_monitor.monitors.index(self.sender().parent().parent())
        prev_model_apps: ModelApps = self.model_apps_manager.get_model_apps_by_index(ui_idx)
        self.connect_monitor(ui_idx, media_sources, prev_model_apps)

    def connect_monitor(self, ui_idx: int, media_sources: tuple, prev_model_apps: Optional[ModelApps] = False):
        label, label_original, label_recording, setup_button, capture_button, duplicate_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        if media_sources[2] is not None:
            if self.tmp_model_apps_container:
                model_apps = self.tmp_model_apps_container[0]
            else:
                model_apps = ModelApps()
            model_apps.update_file_config()
            model_apps.set_media_source(*media_sources)

            if not self.setup_monitor(model_apps):
                if model_apps not in self.tmp_model_apps_container:
                    self.tmp_model_apps_container.append(model_apps)
                return
            else:
                if self.tmp_model_apps_container:
                    self.tmp_model_apps_container.pop()
            
            if prev_model_apps:
                self.delete_monitor(prev_model_apps)
            
            model_apps.signal_image_original.connect(lambda img: self.update_label_image(label_original, img)) # will draw crosshair
            # self.update_label_image(label_original, model_apps.image_resize.copy()) # no crosshair but won't update video
            model_apps.set_draw_polygon = False
            model_apps.image_result.connect(lambda img: self.update_label_image(label, img))
            model_apps.image_result.connect(lambda img: self.update_label_image(label_recording, img, width=self.recorded_image_width))
            model_apps.image_result.connect(lambda img: self.set_image_results(model_apps, img))
            model_apps.create_image_result()
            setup_button.clicked.connect(lambda: self.setup_clicked(media_sources))
            capture_button.clicked.connect(lambda: self.save_image(model_apps))
            delete_button.clicked.connect(lambda: self.delete_monitor(model_apps))
            self.model_apps_manager.set_model_apps(ui_idx, model_apps)

    def update_label_image(self, ui_label, image, width: Optional[int] = "Default", scale_content: bool = False):
        if width == "Default": width = self.image_width
        self.model.show_image_to_label(ui_label, image, width = width, scale_content = scale_content)
    
    def set_image_results(self, model_apps : ModelApps, image):
        self.image_results[model_apps] = image

    def setup_monitor(self, model_apps: ModelApps):
        dialog = SetupDialog(model_apps)
        result = dialog.exec()

        if (result == QtWidgets.QDialog.DialogCode.Accepted): return True

    def delete_monitor(self, model_apps: ModelApps):
        global MAX_MONITOR_INDEX, EMPTY_SLOTS, LATEST_MOVED_WIDGET
        
        ui_idx = self.model_apps_manager.get_index_of_model_apps(model_apps)
        if ui_idx == -1: return
        
        label, label_original, label_recording, setup_button, capture_button, duplicate_button, delete_button = self.get_monitor_ui_by_idx(ui_idx)
        label.clear()
        label.setText(f"{MONITORS_POSITIONS[ui_idx]}")
        label_recording.clear()
        label_recording.setText(f"{MONITORS_POSITIONS[ui_idx]}")
        label_original.clear()
        label_original.setText(f"{MONITORS_POSITIONS[ui_idx]}")
        setup_button.clicked.disconnect()
        capture_button.clicked.disconnect()
        delete_button.clicked.disconnect()

        if model_apps.cap is not None:
            model_apps.timer.stop()
            model_apps.__image_original = None
            model_apps.image = None
            model_apps.image_resize = None
            
            model_apps.reset_config()
            if model_apps.cap is not None and (len(self.model_apps_manager.get_empty_model_apps()) == (MAX_MONITOR_INDEX - 1)):
                try: model_apps.cap.close()
                except: pass
                model_apps.cap = None

        self.model_apps_manager.clear_model_apps(ui_idx)
        LATEST_MOVED_WIDGET[ui_idx] = None
        AVAILABLE_MONITORS[ui_idx] = 0
        EMPTY_SLOTS += 1

    def save_image(self, model_apps : ModelApps):
        dir_save = osp.realpath(osp.join(osp.dirname(__file__), '../../../saved_image/anypoint/'))
        dir_save = osp.join(dir_save, "")
        model_apps.save_image_file(self.image_results[model_apps], dir_save, model_apps.parameter_name)
        print(f'Image saved in {dir_save}!')

    def gallery_clicked(self):
        print("INFO: \"gallery_clicked()\" function is STILL under development!")

    def parameter_clicked(self):
        self.model.form_camera_parameter()

    def original_view_clicked(self):
        if self.ui.stackedWidget.currentIndex():
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.fisheyeButton.setText('Show Original View')
        else:
            self.ui.stackedWidget.setCurrentIndex(1)
            self.ui.fisheyeButton.setText('Show Rectilinear View')
    
    def relayout_grid_clicked(self):
        if self.sender().objectName() == 'layoutOneByOneButton':
            self.grid_monitor.setGridSize(1, 1)
            self.grid_original_monitor.setGridSize(1, 1)
        elif self.sender().objectName() == 'layoutOneByTwoButton':
            self.grid_monitor.setGridSize(1, 2)
            self.grid_original_monitor.setGridSize(1, 2)
        elif self.sender().objectName() == 'layoutTwoByTwoButton':
            self.grid_monitor.setGridSize(2, 2)
            self.grid_original_monitor.setGridSize(2, 2)
        elif self.sender().objectName() == 'layoutTwoByFourButton':
            self.grid_monitor.setGridSize(2, 4)
            self.grid_original_monitor.setGridSize(2, 4)
            
        self.image_width = self.grid_monitor.monitors[0].get_width()
        self.image_width = round(self.image_width / 20) * 20
        [self.model_apps_manager.get_model_apps_by_index(idx).create_image_result() for idx in self.model_apps_manager.get_in_use_model_apps()]

    def handle_swapping(self, sender, receiver):
        sender = int(sender)
        receiver = int(receiver)
        self.model_apps_manager.model_apps[sender], self.model_apps_manager.model_apps[receiver] = self.model_apps_manager.model_apps[receiver], self.model_apps_manager.model_apps[sender]
        self.grid_monitor.monitors[sender], self.grid_monitor.monitors[receiver] = self.grid_monitor.monitors[receiver], self.grid_monitor.monitors[sender]
        self.grid_original_monitor.monitors[sender], self.grid_original_monitor.monitors[receiver] = self.grid_original_monitor.monitors[receiver], self.grid_original_monitor.monitors[sender]
        self.recorder_widget.monitors[sender], self.recorder_widget.monitors[receiver] = self.recorder_widget.monitors[receiver], self.recorder_widget.monitors[sender]
        self.grid_monitor.updateStackedWidget()
        self.grid_monitor.updateButtons()
        self.grid_original_monitor.updateStackedWidget()
        self.grid_original_monitor.updateButtons()
        self.recorder_widget.updateStackedWidget()
        self.recorder_widget.updateButtons()

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
