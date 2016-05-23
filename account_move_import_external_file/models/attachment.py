# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class IrAttachmentMetadata(models.Model):
    _inherit = 'ir.attachment.metadata'

    def _get_file_type(self):
        """Add import move """
        res = super(IrAttachmentMetadata, self)._get_file_type()
        return res + [('imp_mv_ext_loc', 'Import move (ext loc)')]
