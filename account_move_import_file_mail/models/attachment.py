# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class IrAttachmentMetadata(models.Model):
    _inherit = 'ir.attachment.metadata'

    def _get_file_type(self):
        """Add import move from mail """
        res = super(IrAttachmentMetadata, self)._get_file_type()
        return res + [('imp_mv_mail', 'Import move from mail')]

    @api.model
    def message_new(self, msg, custom_values):
        mail_file = super(
         IrAttachmentMetadata, self
            ).message_new(msg, custom_values)
        if mail_file and mail_file.file_type == 'imp_mv_mail':
            ftype = self.env['account.move.import']._check_extension(
                    mail_file.datas_fname)
            sid = self.env['account.move'].multi_move_import(
                mail_file.journal_id,
                mail_file.datas,
                ftype.replace('.', '')
                )
            sid.write({
               'fetchmail_attachment_condition_id':
                      mail_file.fetchmail_attachment_condition_id.id,
                      })

        return mail_file
