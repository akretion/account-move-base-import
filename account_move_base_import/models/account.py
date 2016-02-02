# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# © 2011-2016 Camptocamp SA (code adapted form statement import/completion)
#   @authors Nicolas Bessi, Joel Grand-Guillaume
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import sys
import traceback
import datetime
import psycopg2
import simplejson

from openerp import fields, models, _
from openerp.tools.config import config
from openerp.exceptions import except_orm

from ..parser import new_account_move_parser


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_import_type_selection(self):
        """This is the method to be inherited for adding the imprt type"""
        return [('move_line', 'Move lines')]

    def _get_import_parser_selection(self):
        """This is the method to be inherited for adding the parser"""
        return [('generic_csvxls', 'Generic Csv/Xls')]

    import_ok = fields.Boolean(
            'Used for import',
            help="Check to use this journal to import account move")
    import_type = fields.Selection(
            selection="_get_import_type_selection",
            string='Import type',
            required=False,
            help="Choose here which import type you want to import "
                 "account mouve.")
    import_parser = fields.Selection(
            selection="_get_import_parser_selection",
            string='Import parser',
            required=False,
            help="Choose here which parser you want to import "
                 "account mouve.")
    import_balance_check = fields.Boolean(
            'Balance check',
            help="Balance check befor import account move")


class AccountMove(models.Model):
    _inherit = "account.move"

    def prepare_move_lines_vals(self, parser_vals, move, journal):
        """Hook to build the values of a line from the parser returned values.
        At least it fullfill the move_id. Overide it to add your own
        completion if needed.

        :param dict of vals from parser for account.move.line
          (called by parser.get_mv_line_vals)
        :param move : browse_record of of the concerned account.move
        :param journal : browse_record of of the concerned account.journal
        :return: dict of vals that will be passed to create method of
          move line.
        """
        move_line_obj = self.env['account.move.line']
        act_obj = self.env['account.account']
        values = parser_vals
        values['move_id'] = move.id
        values['journal_id'] = journal.id
        if values.get('account_id', False):
            act_code = values.get('account_id')
            acts = act_obj.search([('code', '=', act_code)])
            if acts:
                values['account_id'] = acts[0].id
            else:
                raise except_orm(
                            _('Invalid data'),
                            _("There is no account with code %s.") %
                            (act_code))
        date = values.get('date')
        period_memoizer = self._context.get('period_memoizer') or {}
        if period_memoizer.get(date):
            values['period_id'] = period_memoizer[date]
        else:
            periods = self.env['account.period'].find(dt=values.get('date'))
            values['period_id'] = periods and periods[0].id or False
            period_memoizer[date] = periods and periods[0].id or False
        values = move_line_obj._add_missing_default_values(values)
        return values

    def prepare_move_vals(self, journal, result_row_list, parser):
        """Hook to build the values of the move from the parser and
        the journal.
        """
        vals = {'journal_id': journal.id}
        vals.update(parser.get_mv_vals())
        return vals

    def multi_move_import(self, journal, file_stream, ftype="csv"):
        """Create multiple moves from values given by the parser for
        the given journal.

        :param account journal: browse_record of the journal used
            to import the file
        :param filebuffer file_stream: binary of the providen file
        :param char: ftype represent the file exstension (csv by default)
        :return: list: list of the created account.mouve
        """
        if not journal:
            raise except_orm(
                _("No acount journal!"),
                _("You must provide a valid acount journal to import an "
                  "account move!"))
        parser = new_account_move_parser(journal, ftype=ftype)
        res = []
        for result_rowjournal_obj_list in parser.parse(file_stream):
            move = self._move_import(
                journal, parser, file_stream, ftype=ftype)
            res.append(move)
        return res

    def _move_import(self, journal, parser, file_stream, ftype="csv"):
        """Create a account move with the given journal and parser. It will
        fullfill the account move with the values of the file providen, but
        will not complete data (like finding the partner, or the right
        analytic account). This will be done in a second step with the
                completion rules.

        :param journal : browse_record of the journal used to import the file
        :param parser: the parser
        :param filebuffer file_stream: binary of the providen file
        :param char: ftype represent the file exstension (csv by default)
        :return: ID of the created account.move
        """
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        attachment_obj = self.env['ir.attachment']
        result_row_list = parser.result_row_list
        # Check all key are present in account.move.line!!
        if not result_row_list:
            raise except_orm(_("Nothing to import"), _("The file is empty"))
        parsed_cols = parser.get_mv_line_vals(result_row_list[0]).keys()
        for col in parsed_cols:
            if col not in move_line_obj._columns:
                raise except_orm(
                    _("Missing column!"),
                    _("Column %s you try to import is not present in the "
                      "move line!") % col)
        move_vals = self.prepare_move_vals(
            journal, result_row_list, parser)
        move = move_obj.create(move_vals)
        try:
            # Record every line in the account move
            move_store = []
            for line in result_row_list:
                parser_vals = parser.get_mv_line_vals(line)
                values = self.prepare_move_lines_vals(
                    parser_vals, move, journal)
                move_store.append(values)
            # TODO add method to wirite extra line : ex countrpart move line
            move_store = parser.add_extra_move_lines(
                move_store, journal, move)
            # Hack to bypass ORM poor perfomance....
            move_line_obj._insert_lines(move_store)
            attachment_data = {
                'name': 'move file',
                'datas': file_stream,
                'datas_fname': "%s.%s" % (datetime.datetime.now().date(),
                                          ftype),
                'res_model': 'account.move',
                'res_id': move,
            }
            attachment_obj.create(attachment_data)
        except Exception:
            error_type, error_value, trbk = sys.exc_info()
            st = "Error: %s\nDescription: %s\nTraceback:" % (
                error_type.__name__, error_value)
            st += ''.join(traceback.format_tb(trbk, 30))
            # TODO we should catch correctly the exception with a python
            # Exception and only re-catch some special exception.
            # For now we avoid re-catching error in debug mode
            if config['debug_mode']:
                raise
            raise except_orm(_("move import error"),
                             _("The move cannot be created: %s") % st)
        return move


class AccountMoveline(models.Model):
    _inherit = "account.move.line"

    def _get_available_columns(self, move_store,
                               include_serializable=False):
        """Return writeable by SQL columns"""
        move_line_obj = self.env['account.move.line']
        model_cols = move_line_obj._columns
        avail = [
            k for k, col in model_cols.iteritems()
        ]
        keys = [k for k in move_store[0].keys() if k in avail]
        # TODO manage sparse fields if exists..
        # if include_serializable:
        #     for k, col in model_cols.iteritems():
        #         if k in move_store[0].keys() and \
        #                 isinstance(col, fields.sparse) and \
        #                 col.serialization_field not in keys and \
        #                 col._type == 'char':
        #             keys.append(col.serialization_field)
        keys.sort()
        return keys

    def _prepare_insert(self, move, cols):
        """ Apply column formating to prepare data for SQL inserting
        Return a copy of move
        """
        st_copy = move
        for k, col in st_copy.iteritems():
            if k in cols:
                st_copy[k] = self._columns[k]._symbol_set[1](col)
        return st_copy

    def _prepare_manyinsert(self, move_store, cols):
        """ Apply column formating to prepare multiple SQL inserts
        Return a copy of move_store
        """
        values = []
        for move in move_store:
            values.append(self._prepare_insert(move, cols))
        return values

    def _serialize_sparse_fields(self, cols, move_store):
        """ Serialize sparse fields values in the target serialized field
        Return a copy of smove_store
        """
        move_line_obj = self.env['account.move.line']
        model_cols = move_line_obj._columns
        sparse_fields = dict(
            [(k, col) for k, col in model_cols.iteritems() if isinstance(
                col, fields.sparse) and col._type == 'char'])
        values = []
        for move in move_store:
            to_json_k = set()
            st_copy = move.copy()
            for k, col in sparse_fields.iteritems():
                if k in st_copy:
                    to_json_k.add(col.serialization_field)
                    serialized = st_copy.setdefault(
                        col.serialization_field, {})
                    serialized[k] = st_copy[k]
            for k in to_json_k:
                st_copy[k] = simplejson.dumps(st_copy[k])
            values.append(st_copy)
        return values

    def _insert_lines(self, move_store):
        """ Do raw insert into database because ORM is awfully slow
            when doing batch write. It is a shame that batch function
            does not exist"""
        move_line_obj = self.env['account.move.line']
        move_line_obj.check_access_rule('create')
        move_line_obj.check_access_rights('create', raise_exception=True)
        cols = self._get_available_columns(
            move_store, include_serializable=True)
        move_store = self._prepare_manyinsert(move_store, cols)
        tmp_vals = (', '.join(cols), ', '.join(['%%(%s)s' % i for i in cols]))
        sql = "INSERT INTO account_move_line (%s) " \
              "VALUES (%s);" % tmp_vals
        try:
            self._cr.executemany(sql, tuple(move_store))
            # TODO handle serialized fields
            # sql, tuple(self._serialize_sparse_fields(cols, move_store)))
        except psycopg2.Error as sql_err:
            self._cr.rollback()
            raise except_orm(_("ORM bypass error"), sql_err.pgerror)

    def _update_line(self, vals):
        """ Do raw update into database because ORM is awfully slow
            when cheking security.
        TODO / WARM: sparse fields are skipped by the method. IOW, if your
        completion rule update an sparse field, the updated value will never
        be stored in the database. It would be safer to call the update method
        from the ORM for records updating this kind of fields.
        """
        cols = self._get_available_columns([vals])
        vals = self._prepare_insert(vals, cols)
        tmp_vals = (', '.join(['%s = %%(%s)s' % (i, i) for i in cols]))
        sql = "UPDATE account_move_line " \
              "SET %s where id = %%(id)s;" % tmp_vals
        try:
            self._cr.execute(sql, vals)
        except psycopg2.Error as sql_err:
            self._cr.rollback()
            raise except_orm(_("ORM bypass error"), sql_err.pgerror)
