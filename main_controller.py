from src.plugin_interface import PluginInterface

from .views.ui_surveillance import Ui_Main
from .views.ui_monitor import Ui_Monitor
from .views.ui_setup import Ui_Setup

from .custom_widgets import *


class Controller(QWidget):
    __deleted_monitors = []

    def __init__(self, model: Model):
        super().__init__()

        self.model = model
        self.ui = Ui_Main()
        self.ui.setupUi(self)

        self.media_manager = {}
        self.canvas_manager = {}

        self.cache = CacheModel()

        self.monitors_widget = PagedStackedWidget()
        self.canvas_widget = PagedStackedWidget(1, 1)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.monitors_widget)
        hlayout.addWidget(self.canvas_widget)
        f = QFrame() 
        f.setLayout(hlayout)

        self.ui.stackedWidget.addWidget(f)
        
        self.canvas_widget.hide()
        self.ui.fisheyeButton.clicked.connect(self.show_canvas)

        pixmap = QPixmap(f'{dir}/resources/welcomelabel.png')
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setPixmap(pixmap)
        self.ui.stackedWidget.addWidget(label)
        self.ui.stackedWidget.setCurrentWidget(label)
        
        self.setup_btn_connect()
        self.set_stylesheet()
        
    def set_stylesheet(self):
        if MOILAPP_VERSION == '4.1.0':
            [button.setStyleSheet(self.model.style_pushbutton()) for button in self.findChildren(QPushButton)]
            [label.setStyleSheet(self.model.style_label()) for label in self.findChildren(QLabel)]
            [slider.setStyleSheet(self.model.style_slider()) for slider in self.findChildren(QSlider)]
            
            [button.setStyleSheet(self.model.style_pushbutton()) for button in self.monitors_widget.findChildren(QPushButton)]
            [label.setStyleSheet(self.model.style_label()) for label in self.monitors_widget.findChildren(QLabel)]

            self.monitors_widget.setStyleSheet(self.model.style_frame_object())
            self.ui.AddButton.setStyleSheet(self.model.style_combobox())
            self.ui.sourceComboBox.setStyleSheet(self.model.style_combobox())

            for monitor in self.monitors_widget.widgets:
                [button.setStyleSheet(self.model.style_pushbutton()) for button in monitor.findChildren(QPushButton)]
                [label.setStyleSheet(self.model.style_label()) for label in monitor.findChildren(QLabel)]
            
            self.ui.recordSourceButton.setStyleSheet(self.model.style_pushbutton_play_pause_video())
        else:
            [button.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet()) for button in self.findChildren(QPushButton)]
            [label.setStyleSheet(self.model.get_stylesheet.label_stylesheet()) for label in self.findChildren(QLabel)]
            [slider.setStyleSheet(self.model.get_stylesheet.slider_stylesheet()) for slider in self.findChildren(QSlider)]
            [button.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet()) for button in self.monitors_widget.findChildren(QPushButton)]
            [label.setStyleSheet(self.model.get_stylesheet.label_stylesheet()) for label in self.monitors_widget.findChildren(QLabel)]
            
            self.monitors_widget.setStyleSheet(self.model.get_stylesheet.frame_object_stylesheet())
            self.ui.AddButton.setStyleSheet(self.model.get_stylesheet.combobox_stylesheet())
            self.ui.sourceComboBox.setStyleSheet(self.model.get_stylesheet.combobox_stylesheet())

            for monitor in self.monitors_widget.widgets:
                [button.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet()) for button in monitor.findChildren(QPushButton)]
                [label.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet()) for label in monitor.findChildren(QLabel)]
            
            self.ui.recordSourceButton.setStyleSheet(self.model.get_stylesheet.pushbutton_play_pause_video_stylesheet())

    def setup_btn_connect(self):
        self.ui.AddButton.on_selection_changed_signal.connect(self.btn_add)
        self.ui.layoutOneByOneButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutOneByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByTwoButton.clicked.connect(self.relayout_grid_clicked)
        self.ui.layoutTwoByFourButton.clicked.connect(self.relayout_grid_clicked)

        self.ui.paramButton.clicked.connect(self.btn_parameter)
        self.ui.recordSourceButton.clicked.connect(self.btn_record)

    def show_canvas(self):
        if self.canvas_widget.isHidden():
            self.canvas_widget.show()
        else:
            self.canvas_widget.hide()

        for m in self.media_manager.values():
            if m.cap is None:
                m.next_frame()

    def btn_add(self, selection):
        if selection == 'Add Monitor' and self.media_manager:
            if len(self.media_manager.keys()) > 1:
                dialog = QDialog()
                combobox = QComboBox()
                combobox.addItems(self.media_manager.keys())
                continue_btn = QPushButton('Continue')
                continue_btn.clicked.connect(dialog.close)
                continue_btn.setMinimumHeight(40)
                vlayout = QVBoxLayout()
                vlayout.addWidget(combobox)
                vlayout.addWidget(continue_btn)
                dialog.setLayout(vlayout)
                
                if MOILAPP_VERSION == '4.1.0':
                    combobox.setStyleSheet(self.model.style_combobox())
                    continue_btn.setStyleSheet(self.model.style_pushbutton())
                else:
                    combobox.setStyleSheet(self.model.get_stylesheet.combobox_stylesheet())
                    continue_btn.setStyleSheet(self.model.get_stylesheet.pushbutton_stylesheet())
                
                dialog.exec()
                
                key = combobox.currentText()
            else:
                key = next(iter(self.media_manager.keys()))
            self.add_monitor(key)
        else:
            self.add_media()
        
    def add_media(self):
        source_type, cam_type, media_source, params_name = self.model.select_media_source()
        if cam_type is not None:    
            media_source_key = media_source.split('/')[-1] if source_type == 'Image/Video' or source_type == 'Load Media' else media_source
            key = ' - '.join([str(i) for i in [source_type, cam_type, media_source_key, params_name]])
            if key not in self.media_manager:
                media_model = MediaModel()
                media_model.set_media_source(source_type, cam_type, media_source, params_name)
                self.media_manager[key] = media_model
                self.ui.sourceComboBox.addItem(key)
            else:
                # TODO If media model was deleted,start it again
                if not self.media_manager[key].timer.isActive():
                    self.media_manager[key].timer.start()
                print("Media source already added, please use add monitor next time")
            self.add_monitor(key)

    def add_monitor(self, key):
        media_model : MediaModel = self.media_manager[key]
        setup = SetupController(media_model)

        # connect setup
        setup.signals.on_change.connect(self.set_map_alpha_beta)
        setup.original_slot= setup.display_label_original
        setup.result_slot= setup.display_label_result
        setup.original_signal = media_model.next_frame_signal.connect(setup.original_slot)
        setup.result_signal = media_model.next_frame_signal.connect(setup.result_slot)
        
        self.set_map_alpha_beta(0, 0, 2.0, 1, setup)

        if media_model.cap is None:
            media_model.next_frame()

        result = setup.exec()
        if not result:
            print('Cancelled')
            # still_exists = 0
            # for m in self.monitors_widget.widgets:
            #     if m.model == media_model:
            #         still_exists = 1

            # if not still_exists:
            #     media_model.timer.stop()
            #     if media_model.cap:
            #         try: media_model.cap.close()
            #         except: media_model.cap.release()
            #         media_model.cap = None
            #         media_model.image = None
            #         media_model.video = None
            return
        else:
            map_x , map_y = setup.map_x , setup.map_y

        monitor = MonitorController(media_model)
        monitor.set_x_y_maps(map_x , map_y)
        self.monitors_widget.addWidget(monitor)
        self.monitors_widget.highlightWidget(monitor)
        self.set_stylesheet()

        self.ui.stackedWidget.setCurrentIndex(0)

        if key not in self.canvas_manager:
            canvas = CanvasController(key, media_model.image)
            self.canvas_widget.addWidget(canvas)
            self.canvas_manager[key] = canvas
        else:
            canvas = self.canvas_manager[key]

        media_model.next_frame_signal.connect(monitor.display_label)
        media_model.next_frame_signal.connect(canvas.setPixmapFromMat)
        media_model.next_frame()

        bbox : BBox = canvas.add_bbox(monitor)
        bbox.zoom = setup.zoom
        bbox.mode = setup.mode
        bbox.signals.on_change.connect(self.set_map_alpha_beta)
        
        if setup.coord is not None:
            bbox.setPosFromCoords(*setup.coord)
    
    def delete_monitor(self, monitor : MonitorController):
        media_model = monitor.model
        self.monitors_widget.widgets.remove(monitor)
        self.monitors_widget.updateStackedWidget()

        # still_exists = 0
        # for m in self.monitors_widget.widgets:
        #     if m.model == media_model:
        #         still_exists = 1

        # if not still_exists:
        #     media_model.timer.stop()
        #     if media_model.cap:
        #         try: media_model.cap.close()
        #         except: media_model.cap.release()
        #         media_model.cap = None
        #         media_model.image = None
        #         media_model.video = None

        # I swear I don't know how to deal with `QThread: Destroyed while thread is still running` without doing this weird thing
        monitor.deleteLater()
        self.__deleted_monitors.append(monitor) 

    def btn_setup(self, target_monitor: MonitorController):
        media_model = target_monitor.model
        setup = SetupController(media_model)
        result = setup.exec()
        if result:
            map_x , map_y = setup.map_x , setup.map_y
            target_monitor.set_x_y_maps(map_x , map_y)
            target_monitor.bbox.zoom = setup.zoom

    def set_map_alpha_beta(self, a, b, z, mode, target, coordinates=False):
        moildev = target.model.moildev

        # Deal with coordinates or the reverse
        if coordinates:
            a, b = moildev.get_alpha_beta(round(a), round(b), mode)
            target.alpha_beta = [a, b]
        else:
            if round(a, 1) == 0.0 and round(b, 1) == 0.0:
                if type(target) == SetupController:
                    target.coord = None
            else:
                # Reverse get_alpha_beta() - Get the specific coordinate image from alpha beta.
                r = moildev.get_rho_from_alpha(a)
                angle = 90 - b
                delta_x = r * math.cos(math.radians(angle))
                delta_y = r * math.sin(math.radians(angle))

                coord_x = round(moildev.icx + delta_x)
                coord_y = round(moildev.icy - delta_y) if mode == 1 else round(delta_y - moildev.icy)

                if type(target) == SetupController:
                    target.coord = (coord_x, coord_y)

        # Deal with Moildev SDK computation
        alpha, beta, zoom = round(a, 1), round(b, 1), round(z, 1)

        # Generate a unique cache key based on the parameters
        cache_key = f'alpha {alpha} beta {beta} zoom {zoom} mode {mode} param {moildev.camera_name}'

        # Retrieve or compute the map coordinates using the Moildev SDK
        map_x, map_y = self.cache.get(cache_key)
        if map_x is None:
            if mode == 1:
                map_x, map_y = moildev.maps_anypoint_mode1(alpha, beta, zoom)
            else:
                map_x, map_y = moildev.maps_anypoint_mode2(alpha, beta, zoom)
            # Store the results in the cache
            self.cache.put(cache_key, (map_x.astype('int16'), map_y.astype('int16')))

        # Ensure the maps are in the correct format
        if map_x.dtype != 'float32':
            map_x, map_y = map_x.astype('float32'), map_y.astype('float32')

        target.set_x_y_maps(map_x.copy(), map_y.copy())

        if type(target) == MonitorController:
            target.alpha = alpha
            target.beta = beta
            target.zoom = zoom
            self.monitors_widget.highlightWidget(target)

    def relayout_grid_clicked(self):
        if self.sender().objectName() == 'layoutOneByOneButton':
            self.monitors_widget.setGridSize(1, 1)
        elif self.sender().objectName() == 'layoutOneByTwoButton':
            self.monitors_widget.setGridSize(1, 2)
        elif self.sender().objectName() == 'layoutTwoByTwoButton':
            self.monitors_widget.setGridSize(2, 2)
        elif self.sender().objectName() == 'layoutTwoByFourButton':
            self.monitors_widget.setGridSize(2, 4)

    def btn_parameter(self):
        key = self.ui.sourceComboBox.currentText()
        if key in self.media_manager:
            self.media_manager[key].form_camera_parameter()
    
    def btn_record(self):
        key = self.ui.sourceComboBox.currentText()
        if key in self.media_manager:
            model_media : MediaModel = self.media_manager[key]
            # model_media.next_frame_signal.connect()
        else:
            if self.ui.recordSourceButton.isChecked():
                self.ui.recordSourceButton.setChecked(False)

        if not os.path.exists(ffmpeg_exe):
            download_file(url_ffmpeg, os.path.join(dir, ffmpeg_file_path))
        
# width = 640
# height = 480
# fps = 30

# ffmpeg_cmd = [
#         ffmpeg_exe,
        # '-y',  # Overwrite output file if it exists
        # '-f', 'rawvideo',  # Input format
        # '-pixel_format', 'yuv420p',  # Pixel format
        # '-video_size', f'{width}x{height}',  # Frame size
        # '-framerate', str(fps),  # Frame rate
        # '-i', '-',  # Input comes from a pipe
        # '-c:v', 'libx264',
        # '-crf', '35',
        # "output.mp4"
    # ]

# ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
# ffmpeg_process.stdin.write(byte_data)
# ffmpeg_process.stdin.close()
# ffmpeg_process.wait()
    def gallery_clicked(self):
        self.ui.fisheyeButton.setText('Show Original View')
        if self.ui.stackedWidget.currentIndex() == 2:
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.galleryButton.setText('Gallery')
        else:
            self.ui.stackedWidget.setCurrentIndex(2)
            self.image_gallery.loadImages()
            self.ui.galleryButton.setText('Go Back')


class NewSurveillance(PluginInterface):
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
