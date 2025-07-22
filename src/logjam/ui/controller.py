from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QSettings
from typing import TYPE_CHECKING, Optional
from logjam.core import FileFilterProcessor, FilterConfig

if TYPE_CHECKING:
    from logjam.ui.app import MainWindow

class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    text_update = pyqtSignal(str)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        result = self.fn(*self.args, **self.kwargs)
        self.signals.finished.emit(result)

class AppController:
    main_window: 'MainWindow'
    threadpool: QThreadPool
    settings: QSettings
    last_opened_file: str
    last_opened_config: str
    file_filter_processor: FileFilterProcessor

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self.threadpool = QThreadPool()
        self.settings = QSettings("LogJam", "LogJamApp")
        self.last_opened_file = self.settings.value("last_opened_file", "")
        self.last_opened_config = self.settings.value("last_opened_config", "")
        self.file_content = ""
        self.file_filter_processor = FileFilterProcessor()
        worker = Worker(self._setup_file_filter_processor)
        worker.signals.finished.connect(self._on_setup_finished)
        self.threadpool.start(worker)

    def open_file(self, file_path: Optional[str] = None):
        if file_path:
            self.last_opened_file = file_path
            self.settings.setValue("last_opened_file", file_path)
            worker = Worker(self._open_file_task)
            worker.signals.text_update.connect(self.main_window.textBrowser.setText)
            self.threadpool.start(worker)

    def load_filters(self, filter_path: Optional[str] = None):
        if filter_path:
            self.last_opened_config = filter_path
            self.settings.setValue("last_opened_config", filter_path)
            worker = Worker(self._load_filters_task)
            worker.signals.text_update.connect(self.main_window.textBrowser.setText)
            self.threadpool.start(worker)

    def _open_file_task(self):
        self.file_filter_processor.file_path = self.last_opened_file
        return self._run_filter_processing()

    def _load_filters_task(self):
        self.file_filter_processor.filter_config = FilterConfig.from_file(self.last_opened_config)
        return self._run_filter_processing()

    def _setup_file_filter_processor(self, config_path: Optional[str] = None, file_path: Optional[str] = None):
        filter_config = FilterConfig.from_file(self.last_opened_config) if self.last_opened_config else None
        self.file_filter_processor = FileFilterProcessor(filter_config, file_path)
        return "File filter processor set up successfully."

    def _on_setup_finished(self, result):
        self.main_window.textBrowser.setText(result)

    def _run_filter_processing(self):
        if not self.file_filter_processor:
            raise ValueError("FileFilterProcessor is not set up.")
        if self.file_filter_processor.file_path and self.file_filter_processor.filter_config:
            filtered_lines = self.file_filter_processor.process_filters(None)
            return "\n".join(str(line) for line in filtered_lines)
        return "No file or filter config loaded."
