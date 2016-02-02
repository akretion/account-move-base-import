# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, _
from openerp.exceptions import except_orm


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_import_type_selection(self):
        """Add remittance type"""
        res = super(AccountJournal, self)._get_import_type_selection()
        return res + [('remittance', 'Remittance')]

    def _get_import_parser_selection(self):
        """Add Csv/Xls remittance Transaction """
        res = super(AccountJournal, self)._get_import_parser_selection()
        return res + [('generic_csvxls_transaction', 'Csv/Xls Transaction')]

    account_commision_id = fields.Many2one(
        "account.account",
        "Commission account")
    account_partner_id = fields.Many2one(
        "account.account",
        "Default Partner account")


class AccountMove(models.Model):
    _inherit = "account.move"

    def prepare_move_lines_vals(self, parser_vals, move, journal):
        """
            Add account_id
        """
        values = super(AccountMove, self).prepare_move_lines_vals(
            parser_vals, move, journal)

        values['move_id'] = move.id
        values['journal_id'] = journal.id

        if not values.get('account_id', False):
            account_id = journal.account_partner_id.id
            if account_id:
                values['account_id'] = account_id
            else:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default partner "
                      "account in the journal %s.") % (journal.name)
                    )
        return values
