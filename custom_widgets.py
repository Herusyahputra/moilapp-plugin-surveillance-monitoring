from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    from src.models.model_apps import Model
    from src.models.moilutils.moildev.Moildev import Moildev
    MOILAPP_VERSION = "4.1.0"
except:
    from src.models.model_apps import ModelApps as Model
    MOILAPP_VERSION = "4.1.1"

from .views.ui_monitor import Ui_Monitor
from .views.ui_setup import Ui_Setup

import numpy as np
import cv2
import os
import time
import math
from .download_ffmpeg import download_file, ffmpeg_file_path, url_ffmpeg

ffmpeg_exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'

dir = os.path.dirname(__file__)
ffmpeg_path = os.path.join(dir, ffmpeg_exe)



calculateBearing = lambda p1, p2: (math.degrees(math.atan2(p2.y() - p1.y(), p2.x() - p1.x())) + 90 + 360) % 360


class AddComboBox(QComboBox):
    on_selection_changed_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItem('Add Monitor')
        self.addItem('Add Media Source')

        # Make the combobox editable but the line edit read-only
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCurrentIndex(-1)
        self.lineEdit().setText('Add')
        self.currentIndexChanged.connect(self.on_selection_changed)
        self.lineEdit().installEventFilter(self)

        self.keyPressEvent = lambda _: None

    def on_selection_changed(self, index):
        if index >= 0:
            selected_text = self.itemText(index)
            self.on_selection_changed_signal.emit(selected_text)
            self.setCurrentIndex(-1)
            self.lineEdit().setText('Add')

    def eventFilter(self, obj, event : QEvent):
        if obj == self.lineEdit() and event.type() == event.Type.MouseButtonRelease:
            self.showPopup()
            return True
        return super().eventFilter(obj, event)


class GalleryWidget(QWidget):
    def __init__(self, folder_path):
        super().__init__()

        # Splitter to manage the layout dynamically
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # QListWidget for displaying image thumbnails
        self.listWidget = QListWidget()
        self.listWidget.setIconSize(QSize(100, 100))
        self.listWidget.setViewMode(QListWidget.ViewMode.IconMode)
        self.listWidget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.listWidget.itemClicked.connect(self.onImageClicked)

        # QLabel for displaying the selected image
        self.imageLabel = QLabel('Select an image from the list')
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.imageLabel.setScaledContents(True)  # Allow QLabel to scale contents
        self.imageLabel.setMinimumSize(200, 200)

        # Add widgets to the splitter
        self.splitter.addWidget(self.listWidget)
        self.splitter.addWidget(self.imageLabel)

        # Set initial sizes: listWidget (1) and imageLabel (1)
        self.splitter.setSizes([400, 400])

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        # Load images from the specified folder
        self.folder_path = folder_path
        self.loadImages()

        # Store the currently displayed image path
        self.currentImagePath = None

    def loadImages(self):
        '''Loads images from the specified folder and adds them to the QListWidget'''
        self.listWidget.clear()
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                image_path = os.path.join(self.folder_path, filename)
                pixmap = QPixmap(image_path)
                icon = QIcon(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

                # Create a QListWidgetItem with the image icon
                item = QListWidgetItem(icon, filename)
                item.setWhatsThis(image_path) # Store the image path in the item

                self.listWidget.addItem(item)

    def onImageClicked(self, item):
        image_path = item.whatsThis()

        if image_path == self.currentImagePath:
            # Clear the QLabel if the same image is clicked
            self.imageLabel.clear()
            self.imageLabel.setText('Select an image from the list')
            self.currentImagePath = None
        else:
            # Display the full-size image
            pixmap = QPixmap(image_path).scaled(self.imageLabel.size(), 
                                                Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
            self.imageLabel.setPixmap(pixmap)
            self.currentImagePath = image_path


class MonitorController(QWidget):
    value_coordinate = pyqtSignal(list)
    swap_signal = pyqtSignal(int, int)
    alpha_beta = []
    enable_hover = True
    enable_drag_drop = True

    cur_index = 0
    alpha = 0
    beta = 0
    zoom = 0
    coord_x = 0
    coord_ = 0

    slots_holder = []
    # delete_slot = None
    # setup_slot = None
    # dup_slot = None
    # label_slot = None
    # capture_slot = None

    map_x = None
    map_y = None
    ori_map_x = None
    ori_map_y = None

    bbox = None

    def __init__(self, model):
        super().__init__()
        self.setMinimumSize(QSize(300, 400))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.setAcceptDrops(True)

        self.ui = Ui_Monitor()
        self.ui.setupUi(self)

        self.model = model

        self.installEventFilter(self)
    
    def display_label(self, image):
        if image is not None and self.isVisible():
            if self.map_x is not None and self.map_y is not None and self.map_x.shape == self.map_y.shape:
                if self.map_x.shape[0] != self.get_width():
                    self.resize_maps()
                image = cv2.remap(image, self.map_x, self.map_y, cv2.INTER_CUBIC)
            self.model.show_image_to_label(self.ui.displayLab, image, self.get_width())

    def resize_maps(self):
        new_width, new_height = self.model.get_new_dimensions(self.ori_map_x, target_width=self.get_width())
        self.map_x = cv2.resize(self.ori_map_x, (new_width, new_height), cv2.INTER_AREA)
        self.map_y = cv2.resize(self.ori_map_y, (new_width, new_height), cv2.INTER_AREA)

    def set_x_y_maps(self, map_x, map_y):
        self.ori_map_x, self.ori_map_y = map_x, map_y
        self.resize_maps()
        if self.model.cap is None:
            self.model.next_frame()

    def get_width(self):
        if self.ui.scrollArea:
            w = self.ui.scrollArea.width()
            w = round(w / 20) * 20
            if w is not None: return w

    def eventFilter(self, obj, event):
        if obj == self and self.enable_hover and self.ui.menuFrame:
            if event.type() == QEvent.Type.Enter:
                self.ui.menuFrame.show()
            elif event.type() == QEvent.Type.Leave:
                self.ui.menuFrame.hide()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.enable_drag_drop:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(self.cur_index))
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint() - self.rect().topLeft())

            self.hide()
            drag.exec(Qt.DropAction.MoveAction)
            self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            sender = int(event.mimeData().text())
            receiver = self.cur_index
            self.swap_signal.emit(sender, receiver)


class PagedStackedWidget(QWidget):
    def __init__(self, rows=2, columns=2):
        super().__init__()
        self.widgets = []
        self.rows = rows
        self.columns = columns
        self.currentIndex = 0
        self.initUI()

    def initUI(self):
        self.stackedPages = QStackedWidget()

        self.prevButton = QPushButton('Previous')
        self.nextButton = QPushButton('Next')
        self.prevButton.setMinimumHeight(40)
        self.nextButton.setMinimumHeight(40)
        self.prevButton.clicked.connect(self.showPrevious)
        self.nextButton.clicked.connect(self.showNext)

        navLayout = QHBoxLayout()
        navLayout.addWidget(self.prevButton)
        navLayout.addWidget(self.nextButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(navLayout)
        mainLayout.addWidget(self.stackedPages)

        self.setLayout(mainLayout)
        self.updateStackedWidget()

    def updateStackedWidget(self):
        while self.stackedPages.count() > 0:
            widget = self.stackedPages.widget(0)
            self.stackedPages.removeWidget(widget)
            widget.deleteLater()

        for i in range(0, len(self.widgets), self.rows * self.columns):
            page = QWidget()
            pageLayout = QGridLayout(page)
            for j in range(self.rows * self.columns):
                row, col = divmod(j, self.columns)
                if i + j < len(self.widgets):
                    pageLayout.addWidget(self.widgets[i + j], row, col)
                    self.widgets[i + j].cur_index = i + j
            page.setLayout(pageLayout)
            self.stackedPages.addWidget(page)
        self.updateButtonVisibility()

## Non wrap around version
    # def showPrevious(self):
    #     if self.currentIndex > 0:
    #         self.currentIndex -= 1
    #     self.stackedPages.setCurrentIndex(self.currentIndex)

    # def showNext(self):
    #     if self.currentIndex < self.stackedPages.count() - 1:
    #         self.currentIndex += 1
    #     self.stackedPages.setCurrentIndex(self.currentIndex)

## Wrap around version
    def showPrevious(self):
        self.currentIndex -= 1
        if self.currentIndex < 0:
            self.currentIndex = self.stackedPages.count() - 1
        self.stackedPages.setCurrentIndex(self.currentIndex)

    def showNext(self):
        self.currentIndex += 1
        if self.currentIndex >= self.stackedPages.count():
            self.currentIndex = 0
        self.stackedPages.setCurrentIndex(self.currentIndex)

    def updateButtonVisibility(self):
        if self.stackedPages.count() <= 1:
            self.nextButton.hide()
            self.prevButton.hide()
        else:
            self.nextButton.show()
            self.prevButton.show()

    def setGridSize(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.updateStackedWidget()

    def addWidget(self, widget):
        if hasattr(widget, 'swap_signal'):
            widget.swap_signal.connect(self.handle_swapping)
        self.widgets.append(widget)
        self.updateStackedWidget()

    def handle_swapping(self, sender, receiver):
        try:
            if 0 <= sender < len(self.widgets) and 0 <= receiver < len(self.widgets):
                self.widgets[sender], self.widgets[receiver] = self.widgets[receiver], self.widgets[sender]
                self.updateStackedWidget()
                self.highlightWidget(self.widgets[receiver])
        except (ValueError, IndexError):
            print(f'Index error in {self.objectName()}')

    def highlightWidget(self, widget):
        if widget in self.widgets:
            widget_index = self.widgets.index(widget)
            page_index = widget_index // (self.rows * self.columns)
            if 0 <= page_index < self.stackedPages.count():
                self.currentIndex = page_index
                self.stackedPages.setCurrentIndex(self.currentIndex)


class BBox(QGraphicsRectItem):
    center_point = (0, 0)
    scale_value = 1.0
    slot_to_disconnect = None
    monitor = None
    zoom = 2.0
    mode = 1

    def __init__(self, rect, image_rect, key, parent=None):
        super().__init__(rect, parent)
        self.image_rect = image_rect
        self.key = key

        self.setBrush(QBrush(QColor(255, 255, 255, 127)))
        self.setPen(QPen(QColor(255, 255, 255, 255)))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        center = self.boundingRect().center()
        self.setTransformOriginPoint(center)

        self.bbox_center_dot = QGraphicsEllipseItem(-5, -5, 40, 40)
        self.bbox_center_dot.setBrush(QBrush(QColor(255, 255, 255)))
        
        self.signals = GenericSignals()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.updateRotation()
        self.doMoildevThing()

    def wheelEvent(self, event):
        super().wheelEvent(event)
        ## Disable zoom by scrolling
        # self.scale_value += -event.delta() * 0.03
        # if self.scale_value < 1:
        #     self.scale_value = 1
        # elif self.scale_value > 2:
        #     self.scale_value = 2
        # self.setScale(self.scale_value)
        # self.doMoildevThing()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.setPos(*self.center_point)
        self.updateDotsPosition(0)
        print(self.center_point)
        self.signals.on_change.emit(0, 0, self.zoom, self.mode, self.monitor, False)

    def setPosFromCoords(self, x, y):
        point = QPointF(x, y)
        rect = self.boundingRect()
        new_position = point - rect.center()
        self.setPos(new_position)
        self.updateRotation()

    def updateRotation(self):
        rect_center = self.sceneBoundingRect().center()
        image_center = self.image_rect.center()
        bearing = calculateBearing(image_center, rect_center)
        self.updateDotsPosition(bearing)

    def doMoildevThing(self):
        point = self.sceneBoundingRect().center().toPoint()
        if self.monitor:
            try:
                x, y, z = round(point.x()), round(point.y()), self.zoom
                # z = round(self.scale_value * 0.5, 1)
                self.signals.on_change.emit(x, y, z, self.mode, self.monitor, True)
            except Exception as e: 
                print(e)
                print(round(point.x()), round(point.y()), self.zoom)

    def updateDotsPosition(self, angle):
        self.setRotation(angle)
        self.bbox_center_dot.setPos(self.sceneBoundingRect().center())

class MediaModel(Model, QObject):
    cap = None
    video = None
    image = None
    next_frame_signal = pyqtSignal(object)
    params_name = None
    
    def __init__(self):
        QObject.__init__(self)
        Model.__init__(self)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def set_media_source(self, source_type, cam_type, media_source, params_name):
        if media_source is None: # I mean this is already checked before so it's safe to remove this? # Eh too lazy/paranoid
            return
        self.moildev = self.connect_to_moildev(parameter_name=params_name)
        resolution = (self.moildev.image_width, self.moildev.image_height)
        
        if source_type == 'Streaming Camera' or source_type == 'Open Camera':
            self.cap = self.moil_camera(cam_type=cam_type, cam_id=media_source, resolution=resolution)
            self.image = self.cap.frame()
        elif source_type == 'Image/Video' or source_type == 'Load Media':
            if media_source.endswith(('.mp4', '.MOV', '.avi')):
                self.cap = cv2.VideoCapture(media_source)
                _, self.image = self.cap.read()
                self.video = True
            elif media_source.endswith(('.jpeg', '.JPG', '.jpg', '.png', 'TIFF')):
                self.image = cv2.imread(media_source)
                # self.init_scene(media_source)

        if self.cap:
            self.timer.start()

        self.params_name = params_name

    def next_frame(self):
        if self.video:
            success, self.image = self.cap.read()
            if not success:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, self.image = self.cap.read()
        elif self.cap:
            self.image = self.cap.frame()
        
        self.next_frame_signal.emit(self.image)

    @staticmethod
    def get_new_dimensions(image, target_width=None, target_height=None):
        original_height, original_width = image.shape[:2]

        if target_width is not None:
            aspect_ratio = original_height / original_width
            new_width = target_width
            new_height = int(target_width * aspect_ratio)
        elif target_height is not None:
            aspect_ratio = original_width / original_height
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        else:
            new_width, new_height = original_width, original_height
        return new_width, new_height

class GenericSignals(QObject):
    result = pyqtSignal(object)
    on_change = pyqtSignal(float, float, float, int, MonitorController, bool)

class Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = GenericSignals()
        self.canceled = False

    @pyqtSlot()
    def run(self):
        if self.canceled:
            return
        result = self.func(*self.args, **self.kwargs)
        if not self.canceled:
            self.signals.result.emit(result)

    def cancel(self):
        self.canceled = True

class CustomThreadPool(QThreadPool):
    def __init__(self, max_threads=8):
        super().__init__()
        self.setMaxThreadCount(max_threads)
        self.pending_tasks = []

    def start(self, runnable: Worker):
        # Cancel any pending tasks
        while len(self.pending_tasks) >= self.maxThreadCount():
            old_task = self.pending_tasks.pop(0)
            old_task.cancel()
        
        self.pending_tasks.append(runnable)
        super().start(runnable)


class CacheModel(Model):
    def __init__(self, maxsize=1000, dir_path=os.path.join(dir, 'cache')):
        # QObject.__init__(self)
        Model.__init__(self)

        self._cache = {}
        self._order = []
        self._capacity = maxsize
        self.dir_path = dir_path

        os.makedirs(dir_path, exist_ok=True)

    @property
    def capacity(self):
        return self._capacity

    @property
    def size(self):
        return len(self._cache)

    def put(self, key, val):
        if key in self._cache:
            return
        elif len(self._cache) >= self._capacity:
            oldest_key = self._order.pop(0)
            self._cache[oldest_key].close()

        self._cache[key] = val
        self._order.append(key)

        filename = f'{self.dir_path}/{key}.npz'
        if not os.path.isfile(filename):
            x, y = val
            np.savez_compressed(filename, map_x=x, map_y=y)

    def get(self, key, default=(None, None)):
        if key in self._cache:
            self._order.remove(key); self._order.append(key)
            return self._cache[key]
        
        filename = f'{self.dir_path}/{key}.npz'
        if os.path.isfile(filename):
            data = np.load(filename)
            x, y = data['map_x'], data['map_y']
            self.put(key, (x, y))
            return (x, y)
        
        return default
    
    def write_to_disk(self, key, x, y):
        filename = f'{self.dir_path}/{key}.npz'
        if os.path.isfile(filename):
            return
        np.savez_compressed(f'{self.dir_path}/{key}.npz', map_x=x, map_y=y)

    def read_from_disk(self, key):
        filename = f'{self.dir_path}/{key}.npz'
        if os.path.isfile(filename):
            data = np.load(filename)
            return data['map_x'], data['map_y']

    def __repr__(self):
        return f"Cache(size : {self.size}, recent keys : {self._order[-3:]})"


class CanvasController(QGraphicsView):
    def __init__(self, key, image, parent=None):
        super().__init__(parent)
        self.key = key
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setSizeAdjustPolicy(QGraphicsView.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        pixmap = QPixmap.fromImage(QImage(image.data, image.shape[1], image.shape[0], QImage.Format.Format_RGB888).rgbSwapped())
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.pixmap_rect = self.pixmap_item.boundingRect()
        self.setSceneRect(0, 0, self.pixmap_rect.width(), self.pixmap_rect.height())

    def setPixmapFromMat(self, image : np.ndarray):
        pixmap = QPixmap.fromImage(QImage(image.data, image.shape[1], image.shape[0], QImage.Format.Format_RGB888).rgbSwapped())
        self.pixmap_item.setPixmap(pixmap)

    def add_bbox(self, monitor):
        rect_width = self.pixmap_rect.width() * 0.2
        rect_height = self.pixmap_rect.height() * 0.2
        rect = QRectF(0, 0, rect_width, rect_height)
        center_x = (self.pixmap_rect.width() - rect_width) / 2
        center_y = (self.pixmap_rect.height() - rect_height) / 2

        bbox_item = BBox(rect, self.pixmap_rect, self.key)
        bbox_item.setPos(center_x, center_y)
        bbox_item.center_point = (center_x, center_y) # for double click

        self.scene.addItem(bbox_item)
        self.scene.addItem(bbox_item.bbox_center_dot)
        bbox_item.updateDotsPosition(0)
        bbox_item.monitor = monitor
        monitor.bbox = bbox_item
        return bbox_item

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class SetupController(QDialog):
    result_signal = None
    original_signal = None
    result_slot = None
    original_slot = None
    map_x = None
    map_y = None
    ori_map_x = None
    ori_map_y = None
    zoom = 2.0
    mode = 1
    coord = (0, 0)
    ratio_x, atio_y = None, None
    image = None
    alpha_beta = [0, 0]

    def __init__(self, model : MediaModel):
        super().__init__()
        self.signals = GenericSignals()
        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.accept_function)
        self.ui.cancelButton.clicked.connect(self.reject_function)

        self.ui.m1Button.setChecked(True)
        self.ui.modeSelectGroup.buttonClicked.connect(self.mode_select_clicked)
        self.mode_select_clicked()
        
        self.ui.topButton.clicked.connect(self.arrow_button_anypoint)
        self.ui.belowButton.clicked.connect(self.arrow_button_anypoint)
        self.ui.centerButton.clicked.connect(self.arrow_button_anypoint)
        self.ui.leftButton.clicked.connect(self.arrow_button_anypoint)
        self.ui.rightButton.clicked.connect(self.arrow_button_anypoint)

        # setup mouse events
        self.ui.label_image_original.mouseReleaseEvent = self.label_original_mouse_release_event
        self.ui.label_image_original.mouseDoubleClickEvent = self.label_original_mouse_double_click_event
        # self.ui.label_image_original.leaveEvent = self.label_original_mouse_leave_event
        # self.ui.label_image_original.mouseMoveEvent = self.label_original_mouse_move_event
        
        # for some reason this make some bugs happen.
        # self.ui.label_image_original.mousePressEvent = self.label_original_mouse_press_event
        

        self.ui.doubleSpinBox_alpha.valueChanged.connect(self.on_change)
        self.ui.doubleSpinBox_beta.valueChanged.connect(self.on_change)
        self.ui.doubleSpinBox_roll.valueChanged.connect(self.on_change)
        self.ui.doubleSpinBox_zoom.valueChanged.connect(self.on_change)

        self.ui.doubleSpinBox_zoom.setValue(2.0)
        
        self.model = model 
        self.set_stylesheet()

        moildev : Moildev = self.model.moildev
        details = [
            f'Camera Name: {moildev.camera_name}',
            f'Camera FOV: {moildev.camera_fov}',
            f'Sensor Width: {moildev.sensor_width}',
            f'Sensor Height: {moildev.sensor_height}',
            f'Image Center X: {moildev.icx}',
            f'Image Center Y: {moildev.icy}',
            f'Ratio: {moildev.ratio}',
            f'Image Width: {moildev.image_width}',
            f'Image Height: {moildev.image_height}',
            f'Calibration Ratio: {moildev.calibration_ratio}',
            f'Parameter 0: {moildev.param_0}',
            f'Parameter 1: {moildev.param_1}',
            f'Parameter 2: {moildev.param_2}',
            f'Parameter 3: {moildev.param_3}',
            f'Parameter 4: {moildev.param_4}',
            f'Parameter 5: {moildev.param_5}',
        ]
        self.ui.label_desc.setText('\n'.join(details))
        
        self.target_width = round(self.ui.label_image_result.width() / 20) * 20

    def set_stylesheet(self):
        if MOILAPP_VERSION == '4.1.0':
            self.ui.label_image_original.setStyleSheet(self.model.style_label())
            self.ui.label_image_result.setStyleSheet(self.model.style_label())
            self.ui.topButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.belowButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.rightButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.leftButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.centerButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.okButton.setStyleSheet(self.model.style_pushbutton())
            self.ui.cancelButton.setStyleSheet(self.model.style_pushbutton())
        else:
            self.ui.label_image_original.setStyleSheet(self.model.get_stylesheet.label_stylesheet())
            self.ui.label_image_result.setStyleSheet(self.model.get_stylesheet.label_stylesheet())
            self.ui.topButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.belowButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.rightButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.leftButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.centerButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.okButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
            self.ui.cancelButton.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())

    def display_label_original(self, image):
        if image is not None:
            w = self.ui.label_image_original.width()
            w = round(w / 20) * 20
            image = self.model.draw_polygon(image.copy(), self.ori_map_x, self.ori_map_y)
            self.model.show_image_to_label(self.ui.label_image_original, image, w)
    
    def display_label_result(self, image):
        if image is not None:
            self.target_width = round(self.ui.label_image_result.width() / 20) * 20
            if self.map_x is not None and self.map_y is not None and self.map_x.shape == self.map_y.shape:
                if self.map_x.shape[0] != self.target_width:
                    self.resize_maps()
                image = cv2.remap(image, self.map_x, self.map_y, cv2.INTER_CUBIC)
            self.model.show_image_to_label(self.ui.label_image_result, image, self.target_width)

    def resize_maps(self):
        new_width, new_height = self.model.get_new_dimensions(self.ori_map_x, target_width=self.target_width)
        self.map_x = cv2.resize(self.ori_map_x, (new_width, new_height), cv2.INTER_AREA)
        self.map_y = cv2.resize(self.ori_map_y, (new_width, new_height), cv2.INTER_AREA)

    def set_x_y_maps(self, map_x, map_y):
        self.ori_map_x, self.ori_map_y = map_x, map_y
        self.resize_maps()
        if self.model.cap is None:
            self.model.next_frame()

    def on_change(self):
        a = self.ui.doubleSpinBox_alpha.value()
        b = self.ui.doubleSpinBox_beta.value()
        self.zoom = self.ui.doubleSpinBox_zoom.value()
        self.signals.on_change.emit(a, b, self.zoom, self.mode, self, False)
    
    def set_alpha_beta(self, a, b, change=True):
        self.ui.doubleSpinBox_alpha.blockSignals(True)
        self.ui.doubleSpinBox_beta.blockSignals(True)
        self.ui.doubleSpinBox_alpha.setValue(round(a, 2))
        self.ui.doubleSpinBox_beta.setValue(round(b, 2))
        self.ui.doubleSpinBox_alpha.blockSignals(False)
        self.ui.doubleSpinBox_beta.blockSignals(False)
        if change:
            self.on_change()

    def set_value_coordinate(self, coordinate: list[float]):
        self.ui.label_pos_x.setText(str(coordinate[0]))
        self.ui.label_pos_y.setText(str(coordinate[1]))

    def mode_select_clicked(self):
        if self.ui.m1Button.isChecked():
            self.ui.doubleSpinBox_roll.hide()
            self.ui.labelRoll.hide()
            self.ui.labelAlpha.setText('Alpha:')
            self.ui.labelBeta.setText('Beta:')
            self.mode = 1
        else:
            self.ui.doubleSpinBox_roll.show()
            self.ui.labelRoll.show()
            self.ui.labelAlpha.setText('Pitch:')
            self.ui.labelBeta.setText('Yaw:')
            self.mode = 2
    
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

    def arrow_button_anypoint(self):
        if self.ui.m1Button.isChecked():
            if self.sender().objectName() == 'topButton':
                self.set_alpha_beta(75, 0)
            elif self.sender().objectName() == 'belowButton':
                self.set_alpha_beta(75, 180)
            elif self.sender().objectName() == 'centerButton':
                self.set_alpha_beta(0, 0)
            elif self.sender().objectName() == 'leftButton':
                self.set_alpha_beta(75, -90)
            elif self.sender().objectName() == 'rightButton':
                self.set_alpha_beta(75, 90)
        else:
            if self.sender().objectName() == 'topButton':
                self.set_alpha_beta(75, 0)
            elif self.sender().objectName() == 'belowButton':
                self.set_alpha_beta(-75, 0)
            elif self.sender().objectName() == 'centerButton':
                self.set_alpha_beta(0, 0)
            elif self.sender().objectName() == 'leftButton':
                self.set_alpha_beta(0, -75)
            elif self.sender().objectName() == 'rightButton':
                self.set_alpha_beta(0, 75)

    def label_original_mouse_release_event(self, event):
        ratio_x, ratio_y = self.model.calculate_ratio_image2label(self.ui.label_image_original, self.model.image)
        x = round(int(event.position().x()) * ratio_x)
        y = round(int(event.position().y()) * ratio_y)
        self.ui.label_pos_x.setText(f'x: {x}')
        self.ui.label_pos_y.setText(f'y: {y}')
        self.coord = (x, y)
        self.signals.on_change.emit(x, y, self.zoom, self.mode, self, True)

        self.set_alpha_beta(self.alpha_beta[0], self.alpha_beta[1], False)

    def label_original_mouse_move_event(self, event):
        pass

    def label_original_mouse_press_event(self, event):
        pass

    def label_original_mouse_double_click_event(self, _):
        pass
        # if self.ui.m1Button.isChecked():
        #     model_apps.label_original_mouse_double_click_anypoint_mode_1()
        # else:
        #     model_apps.label_original_mouse_double_click_anypoint_mode_2()

    # Escape Key does not invoke closeEvent (to disconnect the signals and slots), so need to do it manually
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject_function()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        self.disconnect_signals()
        super().closeEvent(event)

    def reject_function(self):
        self.reject()
        self.close()

    def accept_function(self):
        self.accept()
        self.close()

    def disconnect_signals(self):
        try:
            self.result_signal.disconnect(self.result_slot)
            self.original_signal.disconnect(self.original_slot)
        except Exception as e:
            print(e)
