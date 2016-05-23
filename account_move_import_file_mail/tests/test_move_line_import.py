# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import logging
from StringIO import StringIO
from base64 import b64decode

from .mock_imap import (imap_server_mock)
from .mock_imap import MultiResponse


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
        self.fetchmail_server_model = self.env['fetchmail.server']
        self.fetchmail_condition_model = self.env['fetchmail.attachment.condition']
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
            '../data/incomming_mal.txt'
            )

        self.fetchmail_server_id = self.fetchmail_server_model.create(
            {'name': 'Mock Email server',
             'type': 'imap',
             'server': 'test@imap_test.com',
             'port': 993,
             'user': 'mourad.elhadj.mimoune@imap_akretion.com',
             'password':  'test',
             'is_ssl':  True,
             'object_id': self.ref(
                'attachment_metadata.model_ir_attachment_metadata'),
             })

        self.fetchmail_condition_id = self.fetchmail_condition_model.create(
            {'name': 'Test import move',
             'from_email': 'test_test@akmail.com',
             'server_id': self.fetchmail_server_id.id,
             'mail_subject': 'Import move',
             'type': 'imp_mv_mail',
             'journal_id':  self.bank_journal_id.id,
             'file_extension': 'csv',
             })

        self.email_content = ''
        print self.file_path
        with open(self.file_path, 'r') as content_file:
                    self.email_content = content_file.read()

    def test_00_sftp_import_mv_line(self):
        att_id = self.env['mail.thread'].with_context(
            fetchmail_server_id=self.fetchmail_server_id.id).message_process(
            self.fetchmail_server_id.object_id.model,
            self.email_content,
            save_original=self.fetchmail_server_id.original,
            strip_attachments=(not self.fetchmail_server_id.attach),
            )

        search_file = self.env['ir.attachment.metadata'].search(
            (('name', '=', 'Import move'),))
        self.assertEqual(len(search_file), 1)
        self.assertEqual(search_file[0].id, att_id.id)

        mids = self.env['account.move'].search(
            (('fetchmail_server_id', '=', self.fetchmail_server_id.id),))
        self.assertTrue(
            mids,
            'Move line not imported from '
            'email'
        )
        self.assertEquals(
            len(mids),
            2,
            'Number off Moves imported is not correct'
            )
