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

    def add_extra_move_lines(self, parser, move_store, journal, move):
        """
        Add all extra move by using defaut partner and commission
        account of the journal.

        """
        move_line_obj = self.env['account.move.line']

        account_deb_id = journal.default_debit_account_id.id
        account_cred_id = journal.default_credit_account_id.id

        if parser.transfer_amount > 0.0:
            if not account_deb_id:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default credit or debit"
                      "account for the journal %s.") % (journal.name)
                    )
            transaction_ref = _('Remittance Transfer - %s') % \
                (fields.Date.today(),)
            transfer_mv = {
                    'ref': '/',
                    'name': transaction_ref,
                    'transaction_ref': transaction_ref,
                    'date': fields.Date.today(),
                    'move_id': move.id,
                    'journal_id': journal.id,
                }
            transfer_mv = move_line_obj._add_missing_default_values(
                    transfer_mv)
            transfer_mv['account_id'] = account_deb_id
            transfer_mv['debit'] = parser.transfer_amount - \
                parser.commission_amount
            move_store.append(transfer_mv)

        if parser.refund_amount > 0.0:
            if not account_cred_id:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default credit or debit"
                      "account for the journal %s.") % (journal.name)
                    )
            transaction_ref = _('Remittance Refund - %s') % \
                (fields.Date.today(),)
            refund_mv = {
                    'ref': '/',
                    'name': transaction_ref,
                    'transaction_ref': transaction_ref,
                    'date': fields.Date.today(),
                    'move_id': move.id,
                    'journal_id': journal.id,
                }
            refund_mv = move_line_obj._add_missing_default_values(
                    refund_mv)
            refund_mv['account_id'] = account_cred_id
            refund_mv['credit'] = parser.refund_amount
            move_store.append(refund_mv)

        if parser.commission_amount > 0.0:
            account_com_id = journal.account_commision_id.id
            if not account_com_id:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default commission account"
                      "account for the journal %s.") % (journal.name)
                    )
            commission_ref = _('Remittance Commission -- %s') % \
                (fields.Date.today(),)
            commission_mv = {
                    'ref': '/',
                    'name': commission_ref,
                    'transaction_ref': commission_ref,
                    'date': fields.Date.today(),
                    'move_id': move.id,
                    'journal_id': journal.id,
                }
            commission_mv = move_line_obj._add_missing_default_values(
                    commission_mv)
            commission_mv['account_id'] = account_com_id
            commission_mv['debit'] = parser.commission_amount
            move_store.append(commission_mv)

        return move_store
