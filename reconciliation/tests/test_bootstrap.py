from django.apps import apps
from django.test import SimpleTestCase


class BootstrapConfigurationTests(SimpleTestCase):
    def test_reconciliation_app_is_installed(self) -> None:
        self.assertTrue(apps.is_installed("reconciliation"))

    def test_rest_framework_is_installed(self) -> None:
        self.assertTrue(apps.is_installed("rest_framework"))
