import os
import shutil
import sys
import tempfile
import unittest

if sys.version_info[0] > 2:
    import builtins # pylint: disable=import-error, unused-import
else:
    import __builtin__ # pylint: disable=import-error
    builtins = __builtin__ # pylint: disable=invalid-name

# pylint: disable=wrong-import-position
from mock import patch
from dxlbootstrap.generate.app import DxlBootstrap

class _TempDir(object):
    def __init__(self, prefix, delete_on_exit=True):
        self.prefix = prefix
        self.dir = None
        self.delete_on_exit = delete_on_exit

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="{}_".format(self.prefix))
        return self.dir

    def __exit__(self, exception_type, exception_value, traceback):
        if self.delete_on_exit and self.dir:
            shutil.rmtree(self.dir)

def save_to_file(filename, data):
    with open(filename, 'w') as handle:
        handle.write(data)

APP_CONFIG_FILE = """
[Application]
name=geolocationservice
fullName=Geolocation Service
appClassName=GeolocationService
copyright=Copyright 2018
services=geolocation_service
installRequires=requests

[geolocation_service]
serviceType=/mycompany/service/geolocation
requestHandlers=geolocation_service_hostlookup

[geolocation_service_hostlookup]
topic=/mycompany/service/geolocation/host_lookup
className=GeolocationHostLookupRequestCallback
"""

CLIENT_CONFIG_FILE = """
[Client]
name=geolocationclient
fullName=Geolocation Client
clientClassName=GeolocationClient
copyright=Copyright 2018
includeExampleMethod=yes
"""

class DxlBootstrapTest(unittest.TestCase):
    def test_generate_application_command(self):
        with _TempDir("genapp") as temp_dir, \
            patch.object(builtins, 'print') as mock_print:
            config_file = os.path.join(temp_dir, "application-template.config")
            app_dir = os.path.join(temp_dir, "app")
            save_to_file(config_file, APP_CONFIG_FILE)
            DxlBootstrap().run("application-template",
                               config_file,
                               app_dir)
            mock_print.assert_called_with("Generation succeeded.")
            self.assertTrue(os.path.exists(
                os.path.join(app_dir, "geolocationservice", "app.py")))

    def test_generate_client_command(self):
        with _TempDir("genclient") as temp_dir, \
                patch.object(builtins, 'print') as mock_print:
            config_file = os.path.join(temp_dir, "client-template.config")
            client_dir = os.path.join(temp_dir, "client")
            save_to_file(config_file, CLIENT_CONFIG_FILE)
            DxlBootstrap().run("client-template",
                               config_file,
                               client_dir)
            mock_print.assert_called_with("Generation succeeded.")
            self.assertTrue(os.path.exists(
                os.path.join(client_dir, "geolocationclient", "client.py")))
