from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QSettings
from typing import TYPE_CHECKING, Optional
import logging
from logjam.core import FileFilterProcessor, FilterConfig

if TYPE_CHECKING:
    from logjam.ui.app import MainWindow

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    finished = pyqtSignal(str)


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
    main_window: "MainWindow"
    threadpool: QThreadPool
    settings: QSettings
    last_opened_file: str | None
    filter_file_path: str | None
    file_filter_processor: FileFilterProcessor
    filter_config: FilterConfig | None = None

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.threadpool = QThreadPool()
        self.settings = QSettings("LogJam", "LogJamApp")
        self.last_opened_file = self.settings.value("last_opened_file", "")
        self.file_content = ""
        self.file_filter_processor = FileFilterProcessor()

        logger.info("AppController initialized")
        logger.info(f"Last opened file: {self.last_opened_file}")

        worker = Worker(self._setup_file_filter_processor)
        worker.signals.finished.connect(self._update_text_window)
        self.threadpool.start(worker)

    def open_file(self, file_path: Optional[str] = None):
        if file_path:
            logger.info(f"Opening file: {file_path}")
            self.last_opened_file = file_path
            self.settings.setValue("last_opened_file", file_path)
            worker = Worker(self._open_file_task)
            worker.signals.finished.connect(self._update_text_window)
            self.threadpool.start(worker)
        else:
            logger.warning("open_file called with no file_path")

    def load_filters(self, filter_path: Optional[str] = None):
        if filter_path:
            logger.info(f"Loading filters from: {filter_path}")
            self.filter_file_path = filter_path
            worker = Worker(self._load_filters_task)
            worker.signals.finished.connect(self._update_text_window)
            self.threadpool.start(worker)
        else:
            logger.warning("load_filters called with no filter_path")

    def set_filter_config(self, filter_config: FilterConfig, is_new: bool = False):
        logger.info("Setting filter configuration")
        if is_new:
            logger.debug("Creating new filter configuration")
            self.filter_file_path = None
        self.filter_config = filter_config
        self.file_filter_processor.filter_config = filter_config
        worker = Worker(self._run_filter_processing)
        worker.signals.finished.connect(self._update_text_window)
        self.threadpool.start(worker)

    def _open_file_task(self):
        logger.info(f"Processing file task for: {self.last_opened_file}")
        self.file_filter_processor.file_path = self.last_opened_file
        return self._run_filter_processing()

    def _load_filters_task(self):
        if self.filter_file_path is not None:
            logger.info(f"Loading filter configuration from: {self.filter_file_path}")
            self.filter_config = FilterConfig.from_file(self.filter_file_path)
            self.file_filter_processor.filter_config = self.filter_config
            return self._run_filter_processing()
        else:
            logger.warning("_load_filters_task called but last_opened_config is None")
            return ""

    def _setup_file_filter_processor(
        self, config_path: Optional[str] = None, file_path: Optional[str] = None
    ):
        logger.info("Setting up file filter processor")
        self.file_filter_processor = FileFilterProcessor(self.filter_config, file_path)
        return self._run_filter_processing()

    def _update_text_window(self, result):
        logger.info(f"Updating text window with {len(result)} characters")
        self.main_window.textBrowser.setText(result)

        line_count = len(result.splitlines()) if result else 0
        self.main_window.update_status_bar(line_count=line_count)

    def _run_filter_processing(self):
        if not self.file_filter_processor:
            logger.error("FileFilterProcessor is not set up")
            raise ValueError("FileFilterProcessor is not set up.")

        if (
            self.file_filter_processor.filter_config is not None
            and self.file_filter_processor.file_path is not None
        ):
            logger.info("Running filter processing with config and file path")
            filtered_lines = self.file_filter_processor.process_filters(None)
            result = "\n".join(line.line_content for line in filtered_lines)
            logger.info(
                f"Filter processing completed, {len(filtered_lines)} lines filtered"
            )
            return result
        else:
            logger.info("Skipping filter processing - missing config or file path")
            return ""
