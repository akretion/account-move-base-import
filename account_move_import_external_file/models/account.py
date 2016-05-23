# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    task_id = fields.Many2one('external.file.task', string='Task')
    location_id = fields.Many2one(
        'external.file.location', string='Location',
        related='task_id.location_id', store=True)
