# coding: utf-8
#   @author Sébastien BEAU @ Akretion
#   @author Florian DA COSTA @ Akretion
#   @author Benoit GUILLOT @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FetchmailAttachmentCondition(models.Model):
    _inherit = 'fetchmail.attachment.condition'

    journal_id = fields.Many2one(
        'account.journal',
        'Financial journal to use transaction',
        domain=[('import_ok', '=', True)])

    def get_attachment_metadata_condition_type(self):
        """Add import move """
        res = super(
            FetchmailAttachmentCondition, self
            ).get_attachment_metadata_condition_type()
        return res + [('imp_mv_mail', 'Import move')]
