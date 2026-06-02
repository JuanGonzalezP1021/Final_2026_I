import unittest
import os
import json
from unittest.mock import patch
import config
from controllers.agent_controller import AgentController
from controllers.contact_controller import ContactController

class TestControllerFlow(unittest.TestCase):
    def setUp(self):
        # Redirigir el almacenamiento a /tmp para la prueba
        files_to_mock = (
            'ROSTER_FILE', 'CONTACTS_FILE',
            'PRODUCTIVITY_FILE', 'AUDIT_LOG_FILE'
        )
        for f in files_to_mock:
            path = f'/tmp/test_{f}.json'
            setattr(config, f, path)
            if os.path.exists(path):
                os.remove(path)

    def test_audit_log_emitted(self):
        ac = AgentController()
        
        # Crear un agente
        ac.create({
            'agent_id': 'Agent0001',
            'team_manager': 'TL1',
            'active_date': '2025-01-01',
            'days_range': '0-30',
            'tenurity': 'New Hire'
        })
        
        # Verificar que el archivo de auditoría exista
        self.assertTrue(os.path.exists(config.AUDIT_LOG_FILE))
        
        # Leer y validar la entrada de auditoría
        with open(config.AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f if line.strip()]
            
        self.assertTrue(
            any(e['operation'] == 'CREATE' for e in entries),
            "El log de auditoría no contiene la operación CREATE"
        )