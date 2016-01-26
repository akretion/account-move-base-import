# coding: utf-8
##############################################################################
#
#    account_move_base_import module for Odoo
#    Copyright (C) 2014-2016 Akretion (http://www.akretion.com)
#    @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    some code are refactoing form account_statement_base_completion and
#    account_statement_base_import of Camptocamp SA and ported to v8.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
Wizard to import account move
"""

from openerp import api, fields, models, _
import os


class AcountMovetImporter(models.TransientModel):
    _name = "account.move.import"

    @api.model
    def default_get(self, fields):
        res = super(AcountMovetImporter, self).default_get(fields)
        if (self._context.get('active_model', False) ==
                'account.move' and
                self._context.get('active_ids', False)):
            ids = self._context['active_ids']
            assert len(ids) == 1, 'You cannot use this on more than one '
            'account move !'
            if ids:
                move_obj = self.env['account.move']
                move = move_obj.browse(ids[0])
                res['journal_id'] = move.journal_id.id
                other_vals = self.onchange_journal_id(res['journal_id'])
                res.update(other_vals.get('value', {}))
        return res

    journal_id = fields.Many2one(
        'account.journal',
        'Financial journal to use transaction',
        required=True,
        domain=[('import_ok', '=', True)])
    input_move = fields.Binary('Move file', required=True)

    file_name = fields.Char('File Name', size=128)
    balance_check = fields.Boolean(
        'Balance check',
        help="Balance check befor import")

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        res = {}
        if self.journal_id:
            self.balance_check = self.journal_id.import_balance_check
        return res

    def _check_extension(self, filename):
        (__, ftype) = os.path.splitext(filename)
        if not ftype:
            # We do not use osv exception we do not want to have it logged
            raise Exception(_('Please use a file with an extention'))
        return ftype

    @api.multi
    def import_move(self):
        """This Function import account move line"""
        for importer in self:
            ftype = self._check_extension(importer.file_name)
            sid = self.env['account.move'].multi_move_import(
                importer.journal_id,
                importer.input_move,
                ftype.replace('.', '')
            )
            action_obj = self.env['ir.actions.act_window']
            action_id = self.env.ref('account.action_move_journal_line')
            res = action_obj.read(action_id.id)
            res['domain'] = res['domain'][:-1] + ",('id', 'in', %s)]" % sid
            return res
