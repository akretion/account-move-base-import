# -*- coding: utf-8 -*-
##############################################################################
#    account_move_base_import module for Odoo
#    Copyright (C) 2014-2016 Akretion (http://www.akretion.com)
#    @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    code factoring from account_statement_base_import of Camptocamp SA
#    Author Nicolas Bessi, Joel Grand-Guillaume
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from .parser import new_account_move_parser
from .parser import AccountMoveImportParser
from . import file_parser
from . import generic_file_parser
