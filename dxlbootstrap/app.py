import logging
import os

from threading import RLock
from ConfigParser import ConfigParser
from dxlclient.client import DxlClient
from dxlclient.client_config import DxlClientConfig
from dxlclient.callbacks import EventCallback, RequestCallback
from dxlclient._thread_pool import ThreadPool


# Configure local logger
logger = logging.getLogger(__name__)


class _ThreadedEventCallback(EventCallback):
    """
    Callback wrapper that invokes the wrapped event callback via the specified thread pool
    """
    def __init__(self, callbacks_pool, callback):
        """
        Constructs the callback wrapper
        :param callbacks_pool: The thread pool used to invoke the wrappers
        :param callback: The callback to invoke
        """
        super(_ThreadedEventCallback, self).__init__()
        self._delegate = callback
        self._callbacks_pool = callbacks_pool

    def on_event(self, event):
        """
        Invoked when a DXL event message is received
        :param event: The DXL event message
        """
        self._callbacks_pool.add_task(self._delegate.on_event, event)


class _ThreadedRequestCallback(RequestCallback):
    """
    Callback wrapper that invokes the wrapped request callback via the specified thread pool
    """
    def __init__(self, callbacks_pool, callback):
        super(_ThreadedRequestCallback, self).__init__()
        self._delegate = callback
        self._callbacks_pool = callbacks_pool

    def on_request(self, request):
        """
        Invoked when a DXL request message is received
        :param request: The DXL request message
        """
        self._callbacks_pool.add_task(self._delegate.on_request, request)


class Application(object):
    """
    Base class used for DXL applications.
    """

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
        """
        Constructs the application

        :param config_dir: The directory containing the application configuration files
        :param app_config_file_name: The name of the application-specific configuration file
        """
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
        Validates the configuration files necessary for the application. An exception is thrown
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
        Loads the configuration settings from the application-specific configuration file
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
        """
        Attempts to connect to the DXL fabric
        """
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

        self.on_register_event_handlers()
        self.on_register_services()

        self.on_dxl_connect()

    def run(self):
        """
        Runs the application
        """
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
        """
        Destroys the application (disconnects from fabric, frees resources, etc.)
        """
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
        """
        Unregisters the services associated with the Application from the fabric
        """
        for service in self._services:
            self._dxl_client.unregister_service_sync(service, self.DXL_SERVICE_REGISTRATION_TIMEOUT)

    def _get_callbacks_pool(self):
        """
        Returns the thread pool used to invoke application-specific message callbacks

        :return: The thread pool used to invoke application-specific message callbacks
        """
        with self._lock:
            if self._callbacks_pool is None:
                self._callbacks_pool = ThreadPool(self._callbacks_queue_size,
                                                  self._callbacks_thread_count,
                                                  "CallbacksPool")
            return self._callbacks_pool

    def add_event_callback(self, topic, callback, separate_thread):
        """
        Adds a DXL event message callback to the application.

        :param topic: The topic to associate with the callback
        :param callback: The event callback
        :param separate_thread: Whether to invoke the callback on a thread other than the incoming message
            thread (this is necessary if synchronous requests are made via DXL in this callback).
        """
        if separate_thread:
            callback = _ThreadedEventCallback(self._get_callbacks_pool(), callback)
        self._dxl_client.add_event_callback(topic, callback)

    def add_request_callback(self, service, topic, callback, separate_thread):
        """
        Adds a DXL request message callback to the application.

        :param service: The service to associate the request callback with
        :param topic: The topic to associate with the callback
        :param callback: The request callback
        :param separate_thread: Whether to invoke the callback on a thread other than the incoming message
            thread (this is necessary if synchronous requests are made via DXL in this callback).
        """
        if separate_thread:
            callback = _ThreadedRequestCallback(self._get_callbacks_pool(), callback)
        service.add_topic(topic, callback)

    def register_service(self, service):
        """
        Registers the specified service with the fabric

        :param service: The service to register with the fabric
        """
        self._dxl_client.register_service_sync(service, self.DXL_SERVICE_REGISTRATION_TIMEOUT)
        self._services.append(service)

    def on_run(self):
        """
        Invoked when the application has started running.
        """
        pass

    def on_load_configuration(self, config):
        """
        Invoked after the application-specific configuration has been loaded

        :param config: The application-specific configuration
        """
        pass

    def on_dxl_connect(self):
        """
        Invoked after the client associated with the application has connected
        to the DXL fabric.
        """
        pass

    def on_register_event_handlers(self):
        """
        Invoked when event handlers should be registered with the application
        """
        pass

    def on_register_services(self):
        """
        Invoked when services should be registered with the application
        """
        pass
