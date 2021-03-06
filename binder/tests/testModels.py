from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.test import TestCase, override_settings
from django.db import IntegrityError

from binder import exceptions, models
import os


class Model_BindServer_Tests(TestCase):
    def test_BindServerModel(self):
        """Test that adding a well-formed BindServer works."""
        self.assertEqual(models.BindServer.objects.count(), 0)
        bindserver_1 = models.BindServer(hostname="test1",
                                         control_port=1234)
        bindserver_1.save()
        self.assertEqual(models.BindServer.objects.count(), 1)

    def test_BindServerNonIntControlPort(self):
        """Attempt to add a Bindserver with a non-integer control port."""
        bindserver_1 = models.BindServer(hostname="foo",
                                         control_port="bar1")
        with self.assertRaisesMessage(ValueError, "invalid literal for int() with base 10: 'bar1'"):
            bindserver_1.save()

class Model_Key_Tests(TestCase):
    def test_KeyModel(self):
        """Test that adding a well-formed Key works."""
        self.assertEqual(models.Key.objects.count(), 0)
        key_1 = models.Key(name="testkey1",
                           data="abc123",
                           algorithm="MD5")
        key_1.save()
        self.assertEqual(models.Key.objects.count(), 1)

    def test_NonExistantKey(self):
        with self.assertRaisesMessage(models.Key.DoesNotExist, "Key matching query does not exist"):
            models.Key.objects.get(name="does_not_exist")

    @override_settings(FERNET_KEY='yfE1kyYLNlpR-2ybdB-Mvs_k1ZoDMFFVtE_PpWYxVgs=')
    def test_FernetKeyDecryptionSuccess(self):
        """Test encrypt/decryption when Fernet key is generated by Django."""
        original_tsig_key = 'oGyDayyZ2mDUiJCuTUODnA=='
        key_1 = models.Key(name='testencryptedkey1',
                           data=original_tsig_key,
                           algorithm='MD5')
        key_1.save()
        decrypt_key = Fernet(settings.FERNET_KEY)
        decrypted_tsig_key = decrypt_key.decrypt(bytes(key_1.data))
        self.assertEqual(bytes(original_tsig_key, encoding="utf8"),
                        decrypted_tsig_key)

    @override_settings(FERNET_KEY='yfE1kyYLNlpR-2ybdB-Mvs_k1ZoDMFFVtE_PpWYxVgs=')
    def test_FernetKeyDecryptionFailure(self):
        """Test encrypt/decryption when Fernet key changes."""
        original_tsig_key = 'oGyDayyZ2mDUiJCuTUODnA=='
        key_1 = models.Key(name='testencryptedkey1',
                           data=original_tsig_key,
                           algorithm='MD5')
        key_1.save()
        new_fkey = Fernet(Fernet.generate_key())
        with self.assertRaises(InvalidToken):
            decrypted_tsig_key = new_fkey.decrypt(bytes(key_1.data))
