# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# © 2011-2016 Camptocamp SA (code adapted form statement completion)
#   @authors Nicolas Bessi, Joel Grand-Guillaume
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import sys
from openerp import api, fields, models, _
from openerp.exceptions import except_orm
import inspect
import traceback
import logging

_logger = logging.getLogger(__name__)


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

    function_to_call = fields.Selection(
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

        inv = inv_obj.search(
            [(number_field, '=', mv_line['transaction_ref'].strip()),
                ('type', 'in', type_domain)])
        if inv:
            if len(inv) != 1:
                raise ErrorTooManyPartner(
                    _('Line named "%s" (Ref:%s) was matched by more than one '
                      'partner while looking on %s invoices') %
                    (mv_line['name'], mv_line['transaction_ref'], inv_type))
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
        """Match the partner based on the invoice transaction ID
        and the reference of the move line.
        Then, call the generic get_values_for_line method
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
        """This method will execute the related function setted in journal,
        to retrieve all the values returned by this function that will match.

        :param dict line: read of the concerned account.move.line
        :return:
            A dict of value that can be passed directly to the write method of
            the move line or {}
           {'partner_id': value,
            'account_id: value,
            ...}
        """
        call = self.function_to_call
        if call:
            method_to_call = getattr(self, call)
            if len(inspect.getargspec(method_to_call).args) == 3:
                result = method_to_call(self, line)
            else:
                result = method_to_call(line)
            if result:
                result['already_completed'] = True
                return result
        return None


class AccountMove(models.Model):
    _inherit = "account.move"

    completion_logs = fields.Text('Completion Log', readonly=True)
    import_ok = fields.Boolean(string='Imported',
                               related='journal_id.import_ok',
                               store=True,)

    def write_completion_log(self, move, error_msg, number_imported):
        """Write the log in the completion_logs field of the account move to
        let the user know what have been done. This is an append mode, so we
        don't overwrite what already recoded.
        :param int/long move_id: ID of the account.move
        :param char error_msg: Message to add
        :number_imported int/long: Number of lines that have been completed
        :return True
        """
        user_name = self.env.user.name
        number_line = len(move.line_id)
        log = move.completion_logs
        log = log if log else ""
        completion_date = fields.Date.today()
        message = (_("%s Account move ID %s has %s/%s lines completed by "
                     "%s \n%s\n%s\n") % (completion_date, move.id,
                                         number_imported, number_line,
                                         user_name, error_msg, log))
        move.completion_logs = message

        return True

    @api.multi
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
            journal = move.journal_id
            if journal.import_ok:
                msg_lines = []
                line_ids = tuple((x.id for x in move.line_id))
                res = False
                for line in mv_line_obj.search_read(
                        [('id', 'in', line_ids)],
                        ['name', 'transaction_ref', 'already_completed']):
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
                            mv_line_obj._update_line(res)
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
                            self._cr.commit()
                msg = u'\n'.join(msg_lines)
                self.write_completion_log(move, msg, compl_lines)
            else:
                msg = u' Journal of this move is not used for import '
                compl_lines = 0
                self.write_completion_log(move, msg, compl_lines)
        return True

    @api.multi
    def button_validate(self):
        """
        """
        line_obj = self.env['account.move.line']
        for move in self:
            if move.journal_id.import_ok:
                line_not_already_completed = line_obj.search(
                    [
                        ('move_id', '=', move.id),
                        ('already_completed', '=', False),
                    ],
                    )
                if line_not_already_completed:
                    raise except_orm(
                        _('User error'),
                        _('You should tick Auto-Completed to true for '
                            'all move line of the move %s') % move.name)
        return super(AccountMove, self).button_validate()


class AccountMoveline(models.Model):
    _inherit = "account.move.line"

    already_completed = fields.Boolean(
            "Auto-Completed",
            help="When this checkbox is ticked, the auto-completion "
                 "process/button will ignore this line.")

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
