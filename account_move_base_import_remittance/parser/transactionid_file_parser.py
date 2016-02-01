# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from openerp.tools import ustr
from openerp.addons.account_move_base_import.parser.file_parser \
    import FileParser, float_or_zero


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
