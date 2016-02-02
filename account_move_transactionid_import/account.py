# -*- encoding: utf-8 -*-
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

from openerp import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.Invoice"

    transaction_ref = fields.Char(
            string='Transaction Ref',
            help="Transaction id from the financial institute")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    transaction_ref = fields.Char(
            string='Transaction Ref',
            help="Transaction id from the financial institute")
