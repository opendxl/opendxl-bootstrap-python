import json
import logging

# Configure local logger
logger = logging.getLogger(__name__)


class MessageUtils(object):
    """
    Messaging related utility methods
    """

    @staticmethod
    def dict_to_json(dict, pretty_print=False):
        """
        Converts the specified Python dictionary (``dict``) to a JSON string and
        returns it.

        :param dict: The Python dictionary (``dict``)
        :param pretty_print: Whether to pretty print the JSON
        :return: The JSON string
        """
        if pretty_print:
            return json.dumps(dict, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(dict)

    @staticmethod
    def json_to_dict(json_string):
        """
        Converts the specified JSON string to a Python dictionary (``dict``) and
        returns it.

        :param json_string: The JSON string
        :return: The Python dictionary (``dict``)
        """
        return json.loads(json_string.rstrip("\0"))

    @staticmethod
    def dict_to_json_payload(message, dict, enc="utf-8"):
        """
        Converts the specified Python dictionary (``dict``) to a JSON string and places
        it in the DXL message's payload.

        :param message: The DXL message
        :param dict: The Python dictionary (``dict``)
        :param enc: The encoding to use for the payload
        """
        MessageUtils.encode_payload(message, MessageUtils.dict_to_json(dict), enc)

    @staticmethod
    def json_payload_to_dict(message, enc="utf-8"):
        """
        Converts the specified message's payload from JSON to a Python dictionary (``dict``)
        and returns it.

        :param message: The DXL message
        :param enc: The encoding of the payload
        :return: The Python dictionary (``dict``)
        """
        return MessageUtils.json_to_dict(MessageUtils.decode_payload(message, enc))

    @staticmethod
    def encode_payload(message, value, enc="utf-8"):
        """
        Encodes the specified value and places it in the DXL message's payload

        :param message: The DXL message
        :param value: The value
        :param enc: The encoding to use
        """
        message.payload = MessageUtils.encode(value, enc=enc)

    @staticmethod
    def decode_payload(message, enc="utf-8"):
        """
        Decodes the specified message's payload and returns it.

        :param message: The DXL message
        :param enc: The encoding of the payload
        :return: The decoded value
        """
        return MessageUtils.decode(message.payload, enc=enc)

    @staticmethod
    def encode(value, enc="utf-8"):
        """
        Encodes the specified value and returns it

        :param value: The value
        :param enc: The encoding to use
        :return: The encoded value
        """
        return value.encode(encoding=enc)

    @staticmethod
    def decode(value, enc="utf-8"):
        """
        Decodes the specified value and returns it.

        :param value: The value
        :param enc: The encoding
        :return: The decoded value
        """
        return value.decode(encoding=enc)
