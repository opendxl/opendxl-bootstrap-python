import logging
import os

from threading import RLock
from abc import ABCMeta, abstractmethod
from ConfigParser import ConfigParser
from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.callbacks import EventCallback, RequestCallback
from dxlclient._thread_pool import ThreadPool


# Configure local logger
logger = logging.getLogger(__name__)


class _ThreadedEventCallback(EventCallback):

    def __init__(self, callbacks_pool, callback):
        super(_ThreadedEventCallback, self).__init__()
        self._delegate = callback
        self._callbacks_pool = callbacks_pool

    def on_event(self, event):
        self._callbacks_pool.add_task(self._delegate.on_event, event)


class _ThreadedRequestCallback(RequestCallback):

    def __init__(self, callbacks_pool, callback):
        super(_ThreadedRequestCallback, self).__init__()
        self._delegate = callback
        self._callbacks_pool = callbacks_pool

    def on_request(self, request):
        self._callbacks_pool.add_task(self._delegate.on_request, request)


class Application(object):
    __metaclass__ = ABCMeta

    # The name of the DXL client configuration file
    DXL_CLIENT_CONFIG_FILE = "dxlclient.config"

    # The timeout used when registering/unregistering the service
    DXL_SERVICE_REGISTRATION_TIMEOUT = 60

    # The name of the "IncomingMessagePool" section within the configuration file
    INCOMING_MESSAGE_POOL_CONFIG_SECTION = "IncomingMessagePool"
    # The name of the "MessageCallbackPool" section within the configuration file
    MESSAGE_CALLBACK_POOL_CONFIG_SECTION = "MessageCallbackPool"
    # The property used to specify a queue size
    QUEUE_SIZE_CONFIG_PROP = "queueSize"
    # The property used to specify a thread count
    THREAD_COUNT_CONFIG_PROP = "threadCount"

    # The default thread count for the incoming message pool
    DEFAULT_THREAD_COUNT = 10
    # The default queue size for the incoming message pool
    DEFAULT_QUEUE_SIZE = 1000

    def __init__(self, config_dir, app_config_file_name):
        self._config_dir = config_dir
        self._dxlclient_config_path = os.path.join(config_dir, self.DXL_CLIENT_CONFIG_FILE)
        self._app_config_path = os.path.join(config_dir, app_config_file_name)
        self._epo_by_topic = {}
        self._dxl_client = None
        self._running = False
        self._destroyed = False
        self._services = []

        self._incoming_thread_count = self.DEFAULT_THREAD_COUNT
        self._incoming_queue_size = self.DEFAULT_QUEUE_SIZE

        self._callbacks_pool = None
        self._callbacks_thread_count = self.DEFAULT_THREAD_COUNT
        self._callbacks_queue_size = self.DEFAULT_QUEUE_SIZE

        self._config = None

        self._lock = RLock()

    def __del__(self):
        """destructor"""
        self.destroy()

    def __enter__(self):
        """Enter with"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit with"""
        self.destroy()

    def _validate_config_files(self):
        """
        Validates the configuration files necessary for the ePO service. An exception is thrown
        if any of the required files are inaccessible.
        """
        if not os.access(self._dxlclient_config_path, os.R_OK):
            raise Exception(
                "Unable to access client configuration file: {0}".format(
                    self._dxlclient_config_path))
        if not os.access(self._app_config_path, os.R_OK):
            raise Exception(
                "Unable to access application configuration file: {0}".format(
                    self._app_config_path))

    def _load_configuration(self):
        """
        Loads the configuration settings from the ePO service configuration file
        """
        config = ConfigParser()
        self._config = config
        read_files = config.read(self._app_config_path)
        if len(read_files) is not 1:
            raise Exception(
                "Error attempting to read application configuration file: {0}".format(
                    self._app_config_path))

        #
        # Load incoming pool settings
        #

        try:
            self._incoming_queue_size = config.getint(self.INCOMING_MESSAGE_POOL_CONFIG_SECTION,
                                                      self.QUEUE_SIZE_CONFIG_PROP)
        except:
            pass

        try:
            self._incoming_thread_count = config.getint(self.INCOMING_MESSAGE_POOL_CONFIG_SECTION,
                                                        self.THREAD_COUNT_CONFIG_PROP)
        except:
            pass

        #
        # Load callback pool settings
        #

        try:
            self._callbacks_queue_size = config.getint(self.MESSAGE_CALLBACK_POOL_CONFIG_SECTION,
                                                       self.QUEUE_SIZE_CONFIG_PROP)
        except:
            pass

        try:
            self._callbacks_thread_count = config.getint(self.MESSAGE_CALLBACK_POOL_CONFIG_SECTION,
                                                         self.THREAD_COUNT_CONFIG_PROP)
        except:
            pass

        self.on_load_configuration(config)

    def _dxl_connect(self):
        # Connect to fabric
        config = DxlClientConfig.create_dxl_config_from_file(self._dxlclient_config_path)
        config.incoming_message_thread_pool_size = self._incoming_thread_count
        config.incoming_message_queue_size = self._incoming_queue_size
        logger.info("Incoming message configuration: queueSize={0}, threadCount={1}".format(
            config.incoming_message_queue_size, config.incoming_message_thread_pool_size))
        logger.info("Message callback configuration: queueSize={0}, threadCount={1}".format(
            self._callbacks_queue_size, self._callbacks_thread_count))

        self._dxl_client = DxlClient(config)
        logger.info("Attempting to connect to DXL fabric ...")
        self._dxl_client.connect()
        logger.info("Connected to DXL fabric.")

        self.register_event_handlers()
        self.register_services()

        self.on_dxl_connect()

    def run(self):
        with self._lock:
            if self._running:
                raise Exception("The application is already running")

            self._running = True
            logger.info("Running application ...")

            self.on_run()
            self._validate_config_files()
            self._load_configuration()
            self._dxl_connect()

    def destroy(self):
        with self._lock:
            if self._running and not self._destroyed:
                logger.info("Destroying application ...")
                if self._callbacks_pool is not None:
                    self._callbacks_pool.shutdown()
                if self._dxl_client is not None:
                    self._unregister_services()
                    self._dxl_client.destroy()
                    self._dxl_client = None
                self._destroyed = True

    def _get_path(self, in_path):
        """
        Returns an absolute path for a file specified in the configuration file (supports
        files relative to the configuration file).
        :param in_path: The specified path
        :return: An absolute path for a file specified in the configuration file
        """
        if not os.path.isfile(in_path) and not os.path.isabs(in_path):
            config_rel_path = os.path.join(self._config_dir, in_path)
            if os.path.isfile(config_rel_path):
                in_path = config_rel_path
        return in_path

    def _unregister_services(self):
        for service in self._services:
            self._dxl_client.unregister_service_sync(service, self.DXL_SERVICE_REGISTRATION_TIMEOUT)

    def _get_callbacks_pool(self):
        with self._lock:
            if self._callbacks_pool is None:
                self._callbacks_pool = ThreadPool(self._callbacks_queue_size,
                                                  self._callbacks_thread_count,
                                                  "CallbacksPool")
            return self._callbacks_pool

    def add_event_callback(self, topic, callback, separate_thread):
        if separate_thread:
            callback = _ThreadedEventCallback(self._get_callbacks_pool(), callback)
        self._dxl_client.add_event_callback(topic, callback)

    def add_request_callback(self, service, topic, callback, separate_thread):
        if separate_thread:
            callback = _ThreadedRequestCallback(self._get_callbacks_pool(), callback)
        service.add_topic(topic, callback)

    def register_service(self, service):
        self._dxl_client.register_service_sync(service, self.DXL_SERVICE_REGISTRATION_TIMEOUT)
        self._services.append(service)

    @abstractmethod
    def on_run(self):
        pass

    @abstractmethod
    def on_load_configuration(self, config):
        pass

    @abstractmethod
    def on_dxl_connect(self):
        pass

    def register_event_handlers(self):
        pass

    def register_services(self):
        pass
