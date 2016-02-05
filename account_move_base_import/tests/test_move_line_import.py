# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from openerp.tests.common import TransactionCase
directory = os.path.dirname(__file__)


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

    def test_move_line_file_import(self):
        # test account journal setting for import
        self.bank_journal_id.write(
            dict(
                import_ok=True,
                import_type='move_line',
                import_parser='generic_csvxls',
                ))
        file_name = 'move_line.csv'
        mvl_file_path = os.path.normpath(
            os.path.join(directory, '../data', file_name)
            )
        mvl_file = open(mvl_file_path, 'rb').read().encode('base64')
        importer = self.move_import_model.create(
            dict(
                journal_id=self.bank_journal_id.id,
                input_move=mvl_file,
                file_name=file_name,
                ))
        ftype = importer._check_extension(importer.file_name)
        mids = self.account_move_model.multi_move_import(
                importer.journal_id,
                importer.input_move,
                ftype.replace('.', '')
            )
        self.assertTrue(
            mids,
            'Move line not imported from  %s.' % mvl_file_path
        )
        move_record = mids[0]
        lines = sorted(move_record.line_id, key=lambda x: x.id)
        line1 = lines[0] if lines else False
        self.assertEquals(line1.name, 'move line a', 'name error line 1')
        self.assertEquals(line1.ref, '50969286', 'ref error line 1')
        self.assertEquals(line1.debit, 118.5, 'debit error line 1')
        line2 = lines[1]
        self.assertEquals(line2.name, 'move line b', 'name error line 2')
        self.assertEquals(line2.ref, '51065326', 'ref error line 2')
        self.assertEquals(line2.credit, 98.75, 'debit error line 2')
        line3 = lines[2]
        self.assertEquals(line3.name, 'move line c', 'name error line 3')
        self.assertEquals(line3.ref, '51179306', 'ref error line 3')
        self.assertEquals(line3.credit, 19.75, 'debit error line 3')
        self.assertEquals(
            line1.account_id.code, self.partner_account_id.code,
            "account error for line 1")
        self.assertEquals(
            line2.account_id.code, self.product_account_id.code,
            "account error for line 2")
        self.assertEquals(
            line3.account_id.code, self.tax_account_id.code,
            "account error for line 3")
        move_record.post()
        self.assertEquals(
            move_record.state, 'posted',
            'Account move must be posted')
        self.assertEquals(
            move_record.amount, 268.5,
            "Total amount error for account move")
