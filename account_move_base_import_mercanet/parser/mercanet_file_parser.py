# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from openerp.tools import ustr
from openerp import fields, _
from openerp.exceptions import except_orm
from openerp.addons.account_move_base_import.parser.file_parser \
    import FileParser
from csv import Dialect
from _csv import QUOTE_MINIMAL, register_dialect
from openerp import fields, _
from openerp.exceptions import except_orm

def float_or_zero(val):
    """ Conversion function used to manage
    empty string into float usecase. fro mercanet
    float should / 100 """
    val = val.strip()
    return (float(val.replace(',', '.')) if val else 0.0) / 100.


def format_date(val):
    return datetime.datetime.strptime(val, "%Y%m%d").strftime('%Y-%m-%d')


class mercanet_dialect(Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = '\t'
    quotechar = '"'
    doublequote = False
    skipinitialspace = False
    lineterminator = '\n'
    quoting = QUOTE_MINIMAL
register_dialect("mercanet_dialect", mercanet_dialect)


class MercanetFileParser(FileParser):
    """Mercanet parser that use a define format in csv or xls to import
    account move.
    """

    def __init__(self, parse_name, ftype='csv', **kwargs):
        conversion_dict = {
            "OPERATION_DATE": format_date,
            "PAYMENT_DATE": format_date,
            "TRANSACTION_ID": ustr,
            "OPERATION_NAME": ustr,
            "OPERATION_AMOUNT": float_or_zero,
        }
        self.transfer_amount = None
        self.refund_amount = None
        self.commission_amount = None
        super(MercanetFileParser, self).__init__(
            parse_name, ftype=ftype,
            extra_fields=conversion_dict,
            dialect=mercanet_dialect,
            **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """Used by the new_account_move_parser class factory. Return true if
        the providen name is mercanet_transaction
        """
        return parser_name == 'mercanet_transaction'

    def get_mv_vals(self):
        """This method return a dict of vals that ca be passed to create an
        account move.
        :return: dict of vals that represent additional infos for the move
        """
        return {
            'name': self.move_name or '/',
            'date': self.result_row_list[0]["OPERATION_DATE"] or datetime.now()
        }

    def _pre(self, *args, **kwargs):
        split_file = self.filebuffer.split("\n")
        selected_lines = []
        for line in split_file:
            if line.startswith("FIN"):
                break
            selected_lines.append(line.strip())
        self.filebuffer = "\n".join(selected_lines)

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
            'ref': line.get('TRANSACTION_ID', '/'),
            'name': line.get('PAYMENT_DATE', fields.Date.today()) + ' - ' +
            line.get('TRANSACTION_ID', ''),
            'date': line.get('OPERATION_DATE', fields.Date.today()),
            'transaction_ref': line.get('TRANSACTION_ID', '/'),
            'debit': line.get('debit', 0.0),
            'credit': line.get('credit', 0.0),
        }

    def _post(self, *args, **kwargs):
        """
        Transfer amount to debit or credit depending on OPERATION_NAME
        """

        res = super(MercanetFileParser, self)._post(*args, **kwargs)
        self.transfer_amount = 0.0
        self.refund_amount = 0.0
        self.commission_amount = 0.0
        rows = []

        for row in self.result_row_list:
            if row['OPERATION_NAME'] in ('CREDIT'):
                continue
            rows.append(row)
            if row['OPERATION_NAME'] == 'CREDIT_CAPTURE':
                row["OPERATION_AMOUNT"] = - row["OPERATION_AMOUNT"]
                self.refund_amount += row["OPERATION_AMOUNT"]
                row["debit"] = row["OPERATION_AMOUNT"]
            elif row['OPERATION_NAME'] == 'DEBIT_CAPTURE':
                self.transfer_amount += row["OPERATION_AMOUNT"]
                row["credit"] = row["OPERATION_AMOUNT"]
            else:
                raise except_orm(
                    _("User Error"),
                    _("The acount move imported have invalide line,"
                        "indeed the operation type %s is not supported"
                      ) % row['OPERATION_NAME']
                    )
        self.result_row_list = rows
        return res

    def add_extra_move_lines(self, move_store, journal, move):
        """
        Add all extra move by using defaut partner
        account of the journal.

        """
        move_line_obj = move.env['account.move.line']

        account_deb_id = journal.default_debit_account_id.id
        account_cred_id = journal.default_credit_account_id.id
        import pdb; pdb.set_trace()
        if self.transfer_amount > 0.0:
            if not account_deb_id:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default credit or debit"
                      "account for the journal %s.") % (journal.name)
                    )
            transaction_ref = _('Mercanet Transfer - %s') % \
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
            transfer_mv['debit'] = self.transfer_amount
            move_store.append(transfer_mv)

        if self.refund_amount > 0.0:
            if not account_cred_id:
                raise except_orm(
                    _('Invalid data'),
                    _("There is no default credit or debit"
                      "account for the journal %s.") % (journal.name)
                    )
            transaction_ref = _('Mercanet Refund - %s') % \
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

        return move_store