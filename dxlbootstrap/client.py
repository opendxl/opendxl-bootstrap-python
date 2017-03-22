import logging

from dxlclient.message import Message

# Configure local logger
logger = logging.getLogger(__name__)


class Client(object):
    """
    Base class used for DXL client wrappers.
    """

    # The default amount of time (in seconds) to wait for a response from a DXL service
    _DEFAULT_RESPONSE_TIMEOUT = 30
    # The minimum amount of time (in seconds) to wait for a response from a DXL service
    _MIN_RESPONSE_TIMEOUT = 30

    def __init__(self, dxl_client):
        """
        Constructor parameters:

        :param dxl_client: The DXL client to use for communication with the fabric
        """
        self._dxl_client = dxl_client
        self._response_timeout = self._DEFAULT_RESPONSE_TIMEOUT

    @property
    def response_timeout(self):
        """
        The maximum amount of time (in seconds) to wait for a response from a DXL service
        """
        return self._response_timeout

    @response_timeout.setter
    def response_timeout(self, response_timeout):
        if response_timeout < self._MIN_RESPONSE_TIMEOUT:
            raise Exception("Response timeout must be greater than or equal to " + str(self._MIN_RESPONSE_TIMEOUT))
        self._response_timeout = response_timeout

    def _dxl_sync_request(self, request):
        """
        Performs a synchronous DXL request. Raises an exception if an error occurs.

        :param request: The request to send
        :return: The DXL response
        """
        # Send the request and wait for a response (synchronous)
        res = self._dxl_client.sync_request(request, timeout=self._response_timeout)

        # Return a dictionary corresponding to the response payload
        if res.message_type != Message.MESSAGE_TYPE_ERROR:
            return res
        else:
            raise Exception("Error: " + res.error_message + " (" + str(res.error_code) + ")")
