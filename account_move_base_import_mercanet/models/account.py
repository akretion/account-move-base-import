# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_import_type_selection(self):
        """Add Mercanet type"""
        res = super(AccountJournal, self)._get_import_type_selection()
        return res + [('mercanet', 'Mercanet')]

    def _get_import_parser_selection(self):
        """Add Csv Mercanet Transaction """
        res = super(AccountJournal, self)._get_import_parser_selection()
        return res + [('mercanet_transaction', 'Mercanet Transaction')]
