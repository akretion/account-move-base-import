# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    def get_file_type(self):
        res = super(
            FetchmailServer, self
            ).get_file_type()
        return res + [('imp_mv_mail', 'Import move')]


class FetchmailAttachmentCondition(models.Model):
    _inherit = 'fetchmail.attachment.condition'

    journal_id = fields.Many2one(
        'account.journal',
        'Account journal',
        domain=[('import_ok', '=', True)])

    def get_attachment_metadata_condition_type(self):
        """Add import move """
        res = super(
            FetchmailAttachmentCondition, self
            ).get_attachment_metadata_condition_type()
        return res + [('imp_mv_mail', 'Import move')]
