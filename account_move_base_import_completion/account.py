# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import sys
from openerp import api, fields, models, _
from openerp.exceptions import except_orm
import inspect

class ErrorTooManyPartner(Exception):
    """ New Exception definition that is raised when more than one partner is
    matched by the completion rule.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

    def __repr__(self):
        return repr(self.value)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_functions(self, cr, uid, context=None):
        """List of available methods for auto completion.
        Override this to add you own."""
        return [
            ('get_from_ref_and_invoice',
             'From line reference (based on customer invoice transactionID)'),
        ]

    function_to_call = fields.selection(
        selection="_get_functions",
        string='Auto completion Method',
        help="Choose methode used in auto completion")

    def _find_invoice(self, mv_line, inv_type):
        """Find invoice related to move line"""
        inv_obj = self.env['account.invoice']
        # at the moment we use transaction_id for both supplier and customer
        if inv_type == 'supplier':
            type_domain = ('in_invoice', 'in_refund')
            number_field = 'transaction_id'
        elif inv_type == 'customer':
            type_domain = ('out_invoice', 'out_refund')
            number_field = 'transaction_id'
        else:
            raise except_orm(
                _('System error'),
                _('Invalid invoice type for completion: %') % inv_type)

        inv = inv_obj.search([(number_field, '=', mv_line['ref'].strip()),
                             ('type', 'in', type_domain)])
        if inv:
            if len(inv) != 1:
                raise ErrorTooManyPartner(
                    _('Line named "%s" (Ref:%s) was matched by more than one '
                      'partner while looking on %s invoices') %
                    (mv_line['name'], mv_line['ref'], inv_type))
            return inv
        return False

    def _from_invoice(self, line, inv_type):
        """Populate move line values"""
        if inv_type not in ('supplier', 'customer'):
            raise except_orm(
                _('System error'),
                _('Invalid invoice type for completion: %') %
                inv_type)
        res = {}
        inv = self._find_invoice(line, inv_type)
        if inv:
            partner_id = inv.commercial_partner_id.id
            res = {'partner_id': partner_id,
                   'account_id': inv.account_id.id,
                   'type': inv_type}
        return res

    # Should be private but data are initialised with no update XML
    def get_from_ref_and_supplier_invoice(self, line):
        """Match the partner based on the invoice supplier invoice number and
        the reference of the move line. Then, call the generic
        get_values_for_line method to complete other values. If more than one
        partner matched, raise the ErrorTooManyPartner error.
        :param dict line: read of the concerned account.move.line
        :return:
            A dict of value that can be passed directly to the write method of
            the move line or {}
           {'partner_id': value,
            'account_id': value,
            ...}
        """
        return self._from_invoice(line, 'supplier')

    # Should be private but data are initialised with no update XML
    def get_from_ref_and_invoice(self, line):
        """Match the partner based on the invoice number and the reference of
        the move line. Then, call the generic get_values_for_line method
        to complete other values. If more than one partner matched, raise the
        ErrorTooManyPartner error.
        :param dict line: read of the concerned account.move.line
        :return:
            A dict of value that can be passed directly to the write method of
            the move line or {}
           {'partner_id': value,
            'account_id': value,
            ...}
        """
        return self._from_invoice(line, 'customer')

    def _find_values_from_rules(self, line):
        """This method will execute all related rules, in their sequence order,
        to retrieve all the values returned by the first rules that will match.
        :param calls: list of lookup function name available in rules
        :param dict line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id: value,
            ...}
        """
        call = self.function_to_call
        if call:
            method_to_call = getattr(self, call)
            if len(inspect.getargspec(method_to_call).args) == 3:
                result = method_to_call(call.id, line)
            else:
                result = method_to_call(line)
            if result:
                result['already_completed'] = True
                return result
        return None


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.Multi
    def button_auto_completion(self,):
        """Complete line with values given by rules and tic the
        already_completed checkbox so we won't compute them again unless the
        user untick them!
        """
        mv_line_obj = self.env['account.move.line']
        compl_lines = 0
        mv_line_obj.check_access_rule('create')
        mv_line_obj.check_access_rights(
            'create', raise_exception=True)
        for move in self:
            msg_lines = []
            ctx = context.copy()
            line_ids = tuple((x.id for x in move.line_ids))
            journal = move.journal_id
            res = False
            for line in mv_line_obj.read(line_ids):
                try:
                    # performance trick
                    line['journal_id'] = journal.id
                    res = mv_line_obj._get_line_values_from_rules(
                        line, journal)
                    if res:
                        compl_lines += 1
                except ErrorTooManyPartner, exc:
                    msg_lines.append(repr(exc))
                except Exception, exc:
                    msg_lines.append(repr(exc))
                    error_type, error_value, trbk = sys.exc_info()
                    st = "Error: %s\nDescription: %s\nTraceback:" % (
                        error_type.__name__, error_value)
                    st += ''.join(traceback.format_tb(trbk, 30))
                    _logger.error(st)
                if res:
                    try:
                        mv_line_obj._update_line(
                            cr, uid, res, context=context)
                    except Exception as exc:
                        msg_lines.append(repr(exc))
                        error_type, error_value, trbk = sys.exc_info()
                        st = "Error: %s\nDescription: %s\nTraceback:" % (
                            error_type.__name__, error_value)
                        st += ''.join(traceback.format_tb(trbk, 30))
                        _logger.error(st)
                    # we can commit as it is not needed to be atomic
                    # commiting here adds a nice perfo boost
                    if not compl_lines % 500:
                        cr.commit()
            msg = u'\n'.join(msg_lines)
            self.write_completion_log(cr, uid, move.id,
                                      msg, compl_lines, context=context)
        return True

class AccountMoveline(models.Model):
    _inherit = "account.move.line"

    already_completed = fields.Boolean(
            "Auto-Completed",
            help="When this checkbox is ticked, the auto-completion "
                 "process/button will ignore this line."),

    def _get_line_values_from_rules(self, line, journal):
        """We'll try to find out the values related to the line based
        on completion method setted on the journal.
        We will ignore line for which already_completed
        is ticked.
        :return:
            A dict of dict value that can be passed directly to the write
             method of the account move line or {}. The first dict has move
            line ID as a key: {117009: {'partner_id': 100997,
            'account_id': 489L}}
        """

        if line.get('already_completed'):
            return {}
        # Ask the rule
        vals = journal._find_values_from_rules(line)
        if vals:
            vals['id'] = line['id']
            return vals
        return {}