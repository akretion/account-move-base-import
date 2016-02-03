# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from openerp.tools import ustr
from openerp.addons.account_move_base_import.parser.file_parser \
    import FileParser, float_or_zero
from openerp import fields, _
from openerp.exceptions import except_orm


class TransactionIDFileParser(FileParser):
    """TransactionID parser that use a define format in csv or xls to import
    account move.
    """

    def __init__(self, parse_name, ftype='csv', **kwargs):
        conversion_dict = {
            'ref': ustr,
            'label': ustr,
            'date': datetime.datetime,
            'transaction_id': ustr,
            'amount': float_or_zero,
            'commission_amount': float_or_zero,
            }
        self.transfer_amount = None
        self.refund_amount = None
        self.commission_amount = None
        super(TransactionIDFileParser, self).__init__(
            parse_name, ftype=ftype,
            extra_fields=conversion_dict,
            **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """Used by the new_account_move_parser class factory. Return true if
        the providen name is generic_csvxls_transaction
        """
        return parser_name == 'generic_csvxls_transaction'

    def get_mv_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of account move line in order to record it. It is the
        responsibility of every parser to give this dict of vals, so each one
        can implement his own way of recording the lines.
            :param:  line: a dict of vals that represent a line of
              result_row_list
            :return: dict of values to give to the create method of statement
              line, it MUST contain at least:
                {  'ref': value,
                    'name': value,
                    'date': value,
                    'debit': value,
                    'transaction_ref' : value,
                    'credit': value,
                    'account_id': value,
                }
        """
        return {
            'ref': line.get('ref', '/'),
            'name': line.get('label', line.get('ref', '/')),
            'date': line.get('date', datetime.datetime.now().date()),
            'transaction_ref': line.get('transaction_id', '/'),
            'debit': line.get('debit', 0.0),
            'credit': line.get('credit', 0.0),
        }

    def _post(self, *args, **kwargs):
        """
        Transfer amount to debit or credit depending on its value
        """

        res = super(TransactionIDFileParser, self)._post(*args, **kwargs)
        self.transfer_amount = 0.0
        self.refund_amount = 0.0
        self.commission_amount = 0.0
        rows = []

        for row in self.result_row_list:
            rows.append(row)
            if row['amount'] >= 0.0:
                row["credit"] = row["amount"]
                self.transfer_amount += row["amount"]
            else:
                row["debit"] = -row["amount"]
                self.refund_amount += -row["amount"]
            if row.get("commission_amount"):
                self.commission_amount += row["commission_amount"]
                del row["commission_amount"]
        self.result_row_list = rows
        return res

    def add_extra_move_lines(self, move_store, journal, move):
        """
        Add all extra move by using defaut partner and commission
        account of the journal.

        """
        move_line_obj = move.env['account.move.line']

        account_deb_id = journal.default_debit_account_id.id
        account_cred_id = journal.default_credit_account_id.id

        if self.transfer_amount > 0.0:
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
            transfer_mv['debit'] = self.transfer_amount - \
                self.commission_amount
            move_store.append(transfer_mv)

        if self.refund_amount > 0.0:
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
            refund_mv['credit'] = self.refund_amount
            move_store.append(refund_mv)

        if self.commission_amount > 0.0:
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
            commission_mv['debit'] = self.commission_amount
            move_store.append(commission_mv)

        return move_store
