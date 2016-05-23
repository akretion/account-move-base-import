# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    fetchmail_attachment_condition_id = fields.Many2one(
         'fetchmail.attachment.condition',
         string='FetchMail condition',
         help="The Fetchemail attachment condition used"
              "to create this move")
    fetchmail_server_id = fields.Many2one(
        'fetchmail.server',
        string='Email Server',
        related='fetchmail_attachment_condition_id.server_id', store=True,
        readonly=True,
        help="The email server used to create this move")
