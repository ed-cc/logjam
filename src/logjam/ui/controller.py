from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QSettings
from typing import TYPE_CHECKING, Optional
import logging
from logjam.core import FileFilterProcessor, FilterConfig
from logjam.core.filter_config import Filter

if TYPE_CHECKING:
    from logjam.ui.app import MainWindow

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    finished = pyqtSignal(object)


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
    active_filter_name: str | None = None

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.threadpool = QThreadPool()
        self.settings = QSettings("LogJam", "LogJamApp")
        self.last_opened_file = self.settings.value("last_opened_file", "") or None
        self.filter_file_path = None
        self.file_content = ""
        self.file_filter_processor = FileFilterProcessor()

        logger.info("AppController initialized")
        logger.info(f"Last opened file: {self.last_opened_file}")

    def open_file(self, file_path: Optional[str] = None):
        if file_path:
            logger.info(f"Opening file: {file_path}")
            self.last_opened_file = file_path
            self.settings.setValue("last_opened_file", file_path)
            self._add_recent_file(file_path)
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
        names = filter_config.filter_names()
        self.active_filter_name = names[0] if names else None
        self._reprocess()

    def add_filter(self, filter_obj: Filter):
        """Add a filter to the current config (creating one if needed)."""
        if self.filter_config is None:
            self.filter_config = FilterConfig()
        self.filter_config.add_filter(filter_obj)
        self.file_filter_processor.filter_config = self.filter_config
        self.active_filter_name = filter_obj.name
        self._reprocess()

    def replace_filter(self, old_name: str, new_filter: Filter):
        """Replace an existing filter, e.g. after editing it."""
        if self.filter_config is None:
            raise ValueError("No filter configuration to update")
        self.filter_config.replace_filter(old_name, new_filter)
        self.active_filter_name = new_filter.name
        self._reprocess()

    def remove_filter(self, name: str):
        """Remove a filter and pick a sensible new active filter."""
        if self.filter_config is None:
            return
        self.filter_config.remove_filter(name)
        if self.active_filter_name == name:
            names = self.filter_config.filter_names()
            self.active_filter_name = names[0] if names else None
        self._reprocess()

    def duplicate_filter(self, name: str):
        """Create a copy of an existing filter under a unique name."""
        if self.filter_config is None:
            return
        original = self.filter_config.get_filter_by_name(name)
        copy = Filter.from_dict(original.to_dict())
        copy.name = self._unique_name(f"{name} copy")
        self.add_filter(copy)

    def set_active_filter(self, name: str):
        """Select which filter is applied to the open file."""
        self.active_filter_name = name
        self._reprocess()

    def get_active_filter(self) -> Optional[Filter]:
        if self.filter_config is None or self.active_filter_name is None:
            return None
        try:
            return self.filter_config.get_filter_by_name(self.active_filter_name)
        except ValueError:
            return None

    def _unique_name(self, base: str) -> str:
        if self.filter_config is None:
            return base
        name = base
        counter = 2
        while name in self.filter_config.filters:
            name = f"{base} {counter}"
            counter += 1
        return name

    def _reprocess(self):
        worker = Worker(self._run_filter_processing)
        worker.signals.finished.connect(self._update_text_window)
        self.threadpool.start(worker)

    MAX_RECENT_FILES = 5

    def recent_files(self) -> list[str]:
        """Return the most-recently opened files, newest first."""
        value = self.settings.value("recent_files", [])
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def _add_recent_file(self, file_path: str):
        recent = self.recent_files()
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        del recent[self.MAX_RECENT_FILES :]
        self.settings.setValue("recent_files", recent)

    def _open_file_task(self):
        logger.info(f"Processing file task for: {self.last_opened_file}")
        self.file_filter_processor.file_path = self.last_opened_file
        return self._run_filter_processing()

    def _load_filters_task(self):
        if self.filter_file_path is not None:
            logger.info(f"Loading filter configuration from: {self.filter_file_path}")
            self.filter_config = FilterConfig.from_file(self.filter_file_path)
            self.file_filter_processor.filter_config = self.filter_config
            names = self.filter_config.filter_names()
            self.active_filter_name = names[0] if names else None
            return self._run_filter_processing()
        else:
            logger.warning("_load_filters_task called but last_opened_config is None")
            return ""

    def _update_text_window(self, filtered_lines):
        logger.info(f"Updating text window with {len(filtered_lines)} lines")
        self.main_window.textBrowser.set_filtered_lines(filtered_lines)
        self.main_window.update_status_bar(
            filter_name=self.active_filter_name,
            line_count=len(filtered_lines),
        )
        self.main_window.refresh_filter_panel()

    def _run_filter_processing(self):
        if not self.file_filter_processor:
            logger.error("FileFilterProcessor is not set up")
            raise ValueError("FileFilterProcessor is not set up.")

        if (
            self.file_filter_processor.filter_config is not None
            and self.file_filter_processor.file_path is not None
        ):
            logger.info("Running filter processing with config and file path")
            filtered_lines = self.file_filter_processor.process_filters(
                self.active_filter_name
            )
            logger.info(
                f"Filter processing completed, {len(filtered_lines)} lines filtered"
            )
            return filtered_lines
        else:
            logger.info("Skipping filter processing - missing config or file path")
            return []
