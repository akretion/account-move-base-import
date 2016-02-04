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
        self.account_journal_model = self.env['account.journal']
        self.bank_journal_id = self.account_journal_model.search(
            [('type', '=', 'bank')])[0]

        self.company_id = self.base_user_root.company_id.id
        self.other_user_id_a = self.res_users_model.create(
            {"partner_id": self.other_partner_id.id,
             "company_id": self.company_id,
             "company_ids": [(4, self.company_id)],
             "login": "my_login a",
             "name": "my user",
             "groups_id": [(4, self.ref('account.group_account_manager'))]
             })

    def test_mvl_file_import(self):
        # test account journal setting for import
        self.bank_journal_id.write(
            dict(
                import_ok=True,
                import_type='move_line',
                import_parser='generic_csvxls',
                ))
        mvl_file_path = os.path.normpath(
            os.path.join(directory, '../data'),
            'move_line.csv'
            )
        mvl_file = open(mvl_file_path, 'rb').read().encode('base64')
        importer = self.move_import_model.create(
            dict(journal_id=self.bank_journal_id.id, data_file=mvl_file))
        importer.import_file()
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
        self.assertEquals(move_record.amount, 268.5)
        self.partner_account_id = self.env['account.account'].search(
            [('code', '=', '411100')])[0]

        line = move_record.line_id[0]
        self.assertEquals(line.name, 'move line a')
        self.assertEquals(line.ref, '50969286')
        self.assertEquals(line.account_id.id, self.partner_account_id.id)
