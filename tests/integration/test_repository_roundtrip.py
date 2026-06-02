import os
import tempfile
import unittest
from infrastructure.persistence.json_repository import JsonRepository

class TestRoundtrip(unittest.TestCase):
    def setUp(self):
        # Crear un nombre de archivo temporal único
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.tmp = tmp_file.name
        tmp_file.close()
        # Asegurarse de que el archivo no exista para que el repo lo inicialice
        if os.path.exists(self.tmp):
            os.remove(self.tmp)
        self.repo = JsonRepository(self.tmp, key_field='id')

    def tearDown(self):
        # Limpiar el archivo temporal tras las pruebas
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_insert_read_update_delete(self):
        # Insertar
        self.repo.insert({'id': '1', 'name': 'A'})
        self.assertEqual(self.repo.find_by_key('1')['name'], 'A')

        # Actualizar
        self.repo.update('1', {'id': '1', 'name': 'B'})
        self.assertEqual(self.repo.find_by_key('1')['name'], 'B')

        # Eliminar
        self.assertTrue(self.repo.delete('1'))
        self.assertIsNone(self.repo.find_by_key('1'))