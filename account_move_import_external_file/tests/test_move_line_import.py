# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import logging
from StringIO import StringIO
from base64 import b64decode

from .mock_server import (server_mock)
from .mock_server import MultiResponse


from openerp.tests.common import TransactionCase
directory = os.path.dirname(__file__)


class ContextualStringIO(StringIO):
    """
    snippet from http://bit.ly/1HfH6uW (stackoverflow)
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


class TestMoveLineImport(TransactionCase):
    """ Tests for import account move csv file format
    (account.move.import)
    """

    def setUp(self):
        super(TestMoveLineImport, self).setUp()
        self.move_import_model = self.env['account.move.import']
        self.account_move_model = self.env['account.move']
        self.account_move_line_model = self.env['account.move.line']
        self.account_journal_model = self.env['account.journal']
        self.account_account_model = self.env['account.account']
        self.external_file_task_model = self.env['external.file.task']
        self.external_file_loc_model = self.env['external.file.location']
        self.bank_journal_id = self.account_journal_model.search(
            [('type', '=', 'bank')])[0]
        # check if those accounts exist otherwise create them
        self.partner_account_id = self.account_account_model.search(
            [('code', '=', '411100')])[0]
        self.product_account_id = self.account_account_model.search(
            [('code', '=', '707100')])[0]
        self.tax_account_id = self.account_account_model.search(
            [('code', '=', '445711')])[0]

        if not self.partner_account_id:
            self.partner_account_id = self.account_account_model.create(
                {"code": '411100',
                 "name": "Debtors - (test)",
                 "reconcile": True,
                 "user_type_id":
                 self.ref('account.data_account_type_receivable')
                 })
        if not self.product_account_id:
            self.product_account_id = self.account_account_model.create(
                {"code": '707100',
                 "name": "Product Sales - (test)",
                 "user_type_id":
                 self.ref('account.data_account_type_revenue')
                 })
        if not self.tax_account_id:
            self.tax_account_id = self.account_account_model.create(
                {"code": '445711',
                 "name": "VAT Received - (test)",
                 "user_type_id":
                 self.ref('account.data_account_type_current_liabilities')
                 })

        self.bank_journal_id.write(
            dict(
                import_ok=True,
                import_type='move_line',
                import_parser='generic_csvxls',
                ))
        self.file_path = os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            '../data/move_line.csv'
            )
        self.location_id = self.external_file_loc_model.create(
            {'name': 'Test loc',
             'protocol': 'sftp',
             'address': 'test',
             'login': 'test',
             'password': 'test',
             'host': 'test',
             'port': 22,
             })

        self.task_id = self.external_file_task_model.create(
            {'name': 'Test task',
             'location_id': self.location_id.id,
             'method': 'sftp_import',
             'filename': 'test_imp_move_line.csv',
             'filepath': '/home',
             'file_type': 'imp_mv_ext_loc',
             'journal_id':  self.bank_journal_id.id,
             })

        self.test_file = ContextualStringIO()
        print self.file_path
        with open(self.file_path, 'r') as content_file:
                    content = content_file.read()
                    self.test_file.write(content)
        self.test_file.seek(0)

    def test_00_sftp_import_mv_line(self):
        with server_mock(
            {'exists': True,
             'makedir': True,
             'open': self.test_file,
             'listdir': ['test_imp_move_line.csv']
             }):
            self.task_id.run()
        search_file = self.env['ir.attachment.metadata'].search(
            (('name', '=', 'test_imp_move_line.csv'),))
        self.assertEqual(len(search_file), 1)

        mids = self.env['account.move'].search(
            (('task_id', '=', self.task_id.id),))
        self.assertTrue(
            mids,
            'Move line not imported from '
            'account_move_import_external_file/data/move_line.csv.'
        )
        self.assertEquals(
            len(mids),
            2,
            'Number off Moves imported is not correct'
            )
