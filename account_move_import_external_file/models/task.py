# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields


class Task(models.Model):
    _inherit = 'external.file.task'

    journal_id = fields.Many2one(
        'account.journal',
        'Financial journal to use transaction',
        domain=[('import_ok', '=', True)])

    def _get_file_type(self):
        """Add import move """
        res = super(Task, self)._get_file_type()
        return res + [('imp_mv_ext_loc', 'Import move from external location')]

    @api.multi
    def run(self):
        res = super(Task, self).run()
        for tsk in self:
            if tsk.file_type == 'imp_mv_ext_loc':
                for file_imp in tsk.attachment_ids:
                    ftype = self.env['account.move.import']._check_extension(
                        file_imp.datas_fname)
                    sid = self.env['account.move'].multi_move_import(
                        tsk.journal_id,
                        file_imp.datas,
                        ftype.replace('.', '')
                        )
                    sid.write({'task_id': tsk.id})
        return res
