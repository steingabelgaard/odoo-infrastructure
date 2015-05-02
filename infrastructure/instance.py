# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning
from fabric.api import shell_env
from .server import custom_sudo as sudo
from fabric.contrib.files import exists, append, sed
from ast import literal_eval
import os
import re
from fabric.api import env
import logging
import time
import fabtools
_logger = logging.getLogger(__name__)


class instance(models.Model):

    """"""

    _name = 'infrastructure.instance'
    _description = 'instance'
    _order = 'number'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _states_ = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancel'),
    ]

    number = fields.Integer(
        string='Number',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    database_type_id = fields.Many2one(
        'infrastructure.database_type',
        string='Database Type',
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        copy=False,
        )
    name = fields.Char(
        string='Name',
        compute='get_name',
        store=True,
        )
    sufix = fields.Char(
        string='Sufix',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    # TODO ver que por ahora no los usamos porque los tomamos del dominio
    ssl_certificate = fields.Char(
        string='SSL Certificate',
        )
    ssl_certificate_key = fields.Char(
        string='SSL Certificate KEY',
        )
    advance_type = fields.Selection(
        related='database_type_id.type',
        string='Advance Type'
        )
    type = fields.Selection(
        [(u'secure', u'Secure'), (u'none_secure', u'None Secure')],
        string='Instance Type',
        required=True,
        default='secure',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    db_filter = fields.Many2one(
        'infrastructure.db_filter',
        string='DB Filter',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    limit_time_real = fields.Integer(
        string='Limit Time Real',
        required=True,
        default=240,
        help='Maximum allowed Real time per request. The default odoo value is 120 but sometimes we use 240 to avoid some workers timeout error',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    limit_time_cpu = fields.Integer(
        string='Limit Time CPU',
        required=True,
        default=120,
        help='Maximum allowed CPU time per request. The default odoo value is 60 but sometimes we use 120 to avoid some workers timeout error',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    db_maxconn = fields.Integer(
        string='DB Max connections',
        required=True,
        default=32,
        help='Specify the the maximum number of physical connections to posgresql. Default odoo config is 64, we use 32.',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    note = fields.Html(
        string='Note'
        )
    color = fields.Integer(
        string='Color Index',
        compute='get_color',
        )
    instance_repository_ids = fields.One2many(
        'infrastructure.instance_repository',
        'instance_id',
        string='Repositories',
        copy=True,
        )
    sources_from_id = fields.Many2one(
        'infrastructure.instance',
        compute='get_sources_from',
        string='Other Instance Repositories'
        )
    proxy_mode = fields.Boolean(
        string='Proxy Mode?',
        default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    service_type = fields.Selection([
        ('docker', 'Docker Restart'),
        # ('upstart', 'Upstart Service'),
        ('no_service', 'No Service')],
        default='docker',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    log_level = fields.Selection([
        (u'info', 'info'), (u'debug_rpc', 'debug_rpc'),
        (u'warn', 'warn'), (u'test', 'test'), (u'critical', 'critical'),
        (u'debug_sql', 'debug_sql'), (u'error', 'error'), (u'debug', 'debug'),
        (u'debug_rpc_answer', 'debug_rpc_answer')],
        string='Log Level',
        default='debug_rpc',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    workers = fields.Integer(
        string='Workers',
        default=0,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    admin_pass = fields.Char(
        string='Admin Password',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    unaccent = fields.Boolean(
        string='Enable Unaccent',
        readonly=True,
        default=True,
        states={'draft': [('readonly', False)]},
        )
    module_load = fields.Char(
        string='Load default modules',
        compute='_get_module_load',
        )
    main_hostname = fields.Char(
        string='Main Hostname',
        compute='_get_main_hostname',
        )
    main_hostname_formated = fields.Char(
        string='Main Hostname',
        compute='_get_main_hostname',
        )
    main_hostname_id = fields.Many2one(
        'infrastructure.instance_host',
        string='Main Hostname',
        compute='_get_main_hostname',
        )
    state = fields.Selection(
        _states_,
        string="State",
        default='draft'
        )
    instance_host_ids = fields.One2many(
        'infrastructure.instance_host',
        'instance_id',
        string='Hosts',
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]}
        )
    environment_id = fields.Many2one(
        'infrastructure.environment',
        string='Environment',
        ondelete='cascade',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    database_ids = fields.One2many(
        'infrastructure.database',
        'instance_id',
        string='Databases',
        context={'from_instance': True},
        domain=[('state', '!=', 'cancel')],
        )
    addons_path = fields.Char(
        string='Addons Path',
        compute='_get_addons_path',
        )
    base_path = fields.Char(
        string='Base Path',
        compute='_get_ports_and_paths',
       )
    conf_path = fields.Char(
        string='Config. Path',
        compute='_get_ports_and_paths',
        )
    pg_data_path = fields.Char(
        string='Pg Data Path',
        compute='_get_ports_and_paths',
        )
    conf_file_path = fields.Char(
        string='Config. File Path',
        compute='_get_ports_and_paths',
       )
    backups_path = fields.Char(
        string='Backups Path',
        compute='_get_ports_and_paths',
        )
    data_dir = fields.Char(
        string='Data Dir',
        compute='_get_ports_and_paths',
        )
    logrotate = fields.Boolean(
        string='Logrotate',
        default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    without_demo = fields.Boolean(
        string='Data Dir',
        default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    logfile = fields.Char(
        string='Log File Path',
        compute='_get_ports_and_paths',
        )
    container_logfile = fields.Char(
        string='Log File Path',
        compute='_get_ports_and_paths',
        )
    xml_rpc_port = fields.Integer(
        string='XML-RPC Port',
        compute='_get_ports_and_paths',
        )
    xml_rpcs_port = fields.Integer(
        string='XML-RPCS Port',
        compute='_get_ports_and_paths',
        )
    longpolling_port = fields.Integer(
        string='Longpolling Port',
        compute='_get_ports_and_paths',
        )
    sources_path = fields.Char(
        string='Sources Path',
        compute='_get_ports_and_paths',
        )
    database_count = fields.Integer(
        string='# Databases',
        compute='_get_databases'
        )
    server_id = fields.Many2one(
        'infrastructure.server',
        string='Server',
        related='environment_id.server_id',
        store=True,
        readonly=True
        )
    docker_image_ids = fields.Many2many(
        'infrastructure.docker_image',
        string='Docker Images',
        compute='_get_docker_images',
        )
    odoo_image_id = fields.Many2one(
        'infrastructure.docker_image',
        string='Odoo Image',
        required=True,
        readonly=True,
        domain="[('id', 'in', docker_image_ids[0][2]), ('service', '=', 'odoo')]",
        states={'draft': [('readonly', False)]}
        )
    odoo_image_tag_id = fields.Many2one(
        'infrastructure.docker_image.tag',
        string='Tag',
        required=True,
        readonly=True,
        domain="[('docker_image_id', '=', odoo_image_id)]",
        states={'draft': [('readonly', False)]}
        )
    pg_image_id = fields.Many2one(
        'infrastructure.docker_image',
        string='Postgres Image',
        required=True,
        readonly=True,
        domain="[('odoo_image_ids', '=', odoo_image_id)]",
        states={'draft': [('readonly', False)]}
        )
    pg_image_tag_id = fields.Many2one(
        'infrastructure.docker_image.tag',
        string='Tag',
        required=True,
        readonly=True,
        domain="[('docker_image_id', '=', pg_image_id)]",
        states={'draft': [('readonly', False)]}
        )
    odoo_sufix = fields.Char(
        string='Odoo Sufix',
        help='Commonly used only on debuggin, use for eg. "-u all"'
        )
    odoo_container = fields.Char(
        string='Odoo Container',
        compute='get_container_names',
        store=True,
        )
    pg_container = fields.Char(
        string='Postgresql Container',
        compute='get_container_names',
        )
    # TODO este campo deberia ser un m2o a una clase desde la cual sacamos
    # cuales traemos y cuales no, cambiar logica abajo tmb
    default_repositories_id = fields.Boolean(
        string='Use Default Repositories?',
        # string='Default Repositories',
        default=True,
        # TODO make required
        # required=True,
        )
    # COMMANDS
    update_all_cmd = fields.Char(
        string='Update All',
        compute='get_commands',
        help='If you use this command on terminal you should add\
        -d [database_name] to get it works. You can also add "--logfile=False"\
        if you run it on the terminal to see the log'
        )
    odoo_log_cmd = fields.Char(
        string='Odoo Log',
        compute='get_commands',
        )
    pg_log_cmd = fields.Char(
        string='Postgres Log',
        compute='get_commands',
        )
    update_conf_cmd = fields.Char(
        string='Update Config',
        compute='get_commands',
        )
    start_odoo_cmd = fields.Char(
        string='Start Odoo',
        compute='get_commands',
        )
    start_attach_odoo_cmd = fields.Char(
        string='Start & Attach Odoo',
        compute='get_commands',
        )
    start_attached_odoo_cmd = fields.Char(
        string='Start Attached Container',
        compute='get_commands',
        )
    start_pg_cmd = fields.Char(
        string='Start Postgres',
        compute='get_commands',
        )
    kill_odoo_cmd = fields.Char(
        string='Remove Odoo Container',
        compute='get_commands',
        )
    restart_odoo_cmd = fields.Char(
        string='Restart Odoo',
        compute='get_commands',
        )
    restart_pg_cmd = fields.Char(
        string='Restart Postgres',
        compute='get_commands',
        )
    stop_odoo_cmd = fields.Char(
        string='Stop Odoo',
        compute='get_commands',
        )
    stop_pg_cmd = fields.Char(
        string='Stop Postgres',
        compute='get_commands',
        )
    kill_pg_cmd = fields.Char(
        string='Remove Postgres Container',
        compute='get_commands',
        )
    odoo_version = fields.Char(
        string='Odoo Version',
        compute='get_odoo_version',
        )

    _sql_constraints = [
        ('xml_rpc_port_uniq', 'unique(xml_rpc_port, server_id)',
            'xmlrpc Port must be unique per server!'),
        ('xml_rpcs_port_uniq', 'unique(xml_rpcs_port, server_id)',
            'xmlrpcs Port must be unique per server!'),
        ('longpolling_port_uniq', 'unique(longpolling_port, server_id)',
            'Longpolling Port must be unique per server!'),
        ('logfile_uniq', 'unique(logfile, server_id)',
            'Log File Path must be unique per server!'),
        ('data_dir_uniq', 'unique(data_dir, server_id)',
            'Data Dir must be unique per server!'),
        ('base_path_uniq', 'unique(base_path, server_id)',
            'Base Path must be unique per server!'),
        ('conf_file_path_uniq', 'unique(conf_file_path, server_id)',
            'Config. File Path must be unique per server!'),
        ('number_uniq', 'unique(number, environment_id)',
            'Number must be unique per environment!'),
        ('name_uniq', 'unique(name, environment_id)',
            'Name must be unique per environment!'),
    ]

    @api.one
    @api.depends('state')
    def get_color(self):
        color = 4
        if self.state == 'draft':
            color = 7
        elif self.state == 'cancel':
            color = 1
        self.color = color

    @api.one
    @api.depends('environment_id.odoo_version_id.name')
    def get_odoo_version(self):
        self.odoo_version = self.environment_id.odoo_version_id.name

    @api.one
    @api.depends('database_type_id')
    def get_sources_from(self):
        sources_from_id = False
        db_type = self.database_type_id
        if db_type.sources_from_id:
            sources_from_id = self.search([
                ('database_type_id', '=', db_type.sources_from_id.id),
                ('environment_id', '=', self.environment_id.id),
                ], limit=1)
        self.sources_from_id = sources_from_id

    @api.one
    @api.depends('server_id')
    def _get_main_hostname(self):
        main_host = self.instance_host_ids.filtered(
            lambda r: r.type == 'main')
        if not main_host:
            main_host = self.instance_host_ids.filtered(
                lambda r: r.type == 'other')
        if main_host:
            if self.type == 'secure':
                main_hostname = 'https://%s:443' % main_host[0].name
            else:
                main_hostname = 'http://%s' % main_host[0].name
            self.main_hostname = main_hostname
            self.main_hostname_id = main_host[0].id

    @api.one
    @api.depends('server_id')
    def _get_docker_images(self):
        self.docker_image_ids = self.env['infrastructure.docker_image']
        self.docker_image_ids = [
            x.docker_image_id.id for x in self.server_id.server_docker_image_ids]

    @api.one
    @api.depends(
        'database_type_id.prefix',
        'environment_id.name',
        'sufix',
        )
    def get_name(self):
        self.name = "%s-%s%s" % (
            self.environment_id.name or '',
            self.database_type_id.prefix or '',
            self.sufix and '_' + self.sufix or '',
            )

    @api.onchange('database_type_id')
    def onchange_database_type_id(self):
        if self.database_type_id:
            instance_admin_pass = self.database_type_id.instance_admin_pass
            if self.server_id.server_use_type == 'own' and instance_admin_pass:
                admin_pass = instance_admin_pass or self.name
            else:
                admin_pass = self.name
            self.admin_pass = admin_pass
            self.db_filter = self.database_type_id.db_filter
            self.service_type = self.database_type_id.service_type

    @api.one
    @api.depends('name')
    def get_container_names(self):
        self.odoo_container = 'odoo-' + self.name
        self.pg_container = 'db-' + self.name

    @api.multi
    def show_passwd(self):
        raise except_orm(
            _("Password for user"),
            _("%s") % self.admin_pass
        )

    @api.multi
    def action_wfk_set_draft(self):
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.one
    @api.constrains('number')
    def _check_number(self):
        if not self.number or self.number < 1 or self.number > 9:
            raise Warning(_('Number should be between 1 and 9'))

    @api.one
    def unlink(self):
        if self.state not in ('draft', 'cancel'):
            raise Warning(_(
                'You cannot delete an instance which \
                is not draft or cancelled.'))
        return super(instance, self).unlink()

# Calculated fields
    @api.one
    @api.depends('environment_id')
    def _get_module_load(self):
        module_load = ','.join(
            [x.repository_id.server_wide_modules for x in self.instance_repository_ids if x.repository_id.server_wide_modules])
        if module_load:
            self.module_load = 'web,web_kanban,' + module_load

    @api.one
    @api.depends('database_ids')
    def _get_databases(self):
        self.database_count = len(self.database_ids)

    @api.multi
    def repositories_pull_clone_and_checkout(self):
        self.instance_repository_ids.repository_pull_clone_and_checkout(
            update=True)

    @api.multi
    def add_repositories(self):
        _logger.info("Adding Repositories")
        # TODO cambiar cuando hagamos el campo este m2o y no bolean
        if self.default_repositories_id:
            branch_id = self.environment_id.odoo_version_id.default_branch_id.id
            instance_actual_repository_ids = [
                x.repository_id.id for x in self.instance_repository_ids]
            repositories = self.env['infrastructure.repository'].search([
                ('default_in_new_env', '=', 'True'),
                ('branch_ids', '=', branch_id),
                ('id', 'not in', instance_actual_repository_ids),
                ])

            for repository in repositories:
                vals = {
                    'repository_id': repository.id,
                    'branch_id': branch_id,
                    'instance_id': self.id,
                }
                self.instance_repository_ids.create(vals)

    @api.one
    @api.depends(
        'instance_repository_ids.repository_id.addons_path',
    )
    def _get_addons_path(self):
        _logger.info("Getting Addons Path")
        addons_paths = [
            x.repository_id.addons_path for x in self.instance_repository_ids if x.repository_id.addons_path]
        self.addons_path = ','.join(addons_paths)

    @api.onchange('environment_id')
    def _onchange_environment(self):
        # Get same env instances for database type and instance number
        instances = self.search(
            [('environment_id', '=', self.environment_id.id)],
            order='number desc',
            )
        actual_db_type_ids = [x.database_type_id.id for x in instances]
        self.number = instances and instances[0].number + 1 or 1
        self.database_type_id = self.env[
            'infrastructure.database_type'].search(
                [('id', 'not in', actual_db_type_ids)],
                limit=1
                )

        # Set workers
        if self.database_type_id.workers == 'clasic_rule':
            number_of_processors = self.environment_id.server_id.number_of_processors
            self.workers = (number_of_processors * 2) + 1
        else:
            self.workers = self.database_type_id.workers_number

        # get docker images
        docker_image_ids = [
            x.docker_image_id.id for x in self.environment_id.server_id.server_docker_image_ids]
        docker_images = self.env['infrastructure.docker_image']
        odoo_images = docker_images.search([
            ('service', '=', 'odoo'),
            ('id', 'in', docker_image_ids),
            ('odoo_version_id', '=', self.environment_id.odoo_version_id.id)
            ], limit=1)
        self.odoo_image_id = odoo_images

    @api.onchange('odoo_image_id')
    def _onchange_docker_image(self):
        tags = self.odoo_image_id.tag_ids
        pg_images = self.odoo_image_id.pg_image_ids
        self.odoo_image_tag_id = tags and tags[0] or False
        self.pg_image_id = pg_images and pg_images[0] or False

    @api.onchange('pg_image_id')
    def _onchange_pg_image(self):
        self.pg_image_tag_id = self.pg_image_id.tag_ids and self.pg_image_id.tag_ids[0] or False

    @api.one
    @api.depends('name', 'number', 'environment_id')
    def _get_ports_and_paths(self):
        xml_rpc_port = False
        xml_rpcs_port = False
        longpolling_port = False
        conf_path = False
        conf_file_path = False
        backups_path = False
        base_path = False
        pg_data_path = False
        logfile = False
        data_dir = False
        sources_path = False
        if self.environment_id.number and self.number:
            prefix = str(self.environment_id.number) + str(self.number)
            xml_rpc_port = int(prefix + '1')
            xml_rpcs_port = int(prefix + '2')
            longpolling_port = int(prefix + '3')
        self.xml_rpc_port = xml_rpc_port
        self.xml_rpcs_port = xml_rpcs_port
        self.longpolling_port = longpolling_port
        if self.environment_id.path and self.database_type_id.prefix:
            path_sufix = self.database_type_id.prefix + (self.sufix and '_' + self.sufix or '')
            base_path = os.path.join(
                self.environment_id.path, path_sufix)
            conf_path = os.path.join(base_path, 'config')
            pg_data_path = os.path.join(base_path, 'postgresql')
            backups_path = os.path.join(
                self.server_id.backups_path,
                self.environment_id.name,
                self.database_type_id.prefix,
                )
            conf_file_path = os.path.join(conf_path, 'openerp-server.conf')
            logfile = os.path.join(conf_path, 'odoo.log')
            data_dir = os.path.join(base_path, 'data_dir')
            sources_path = os.path.join(base_path, 'sources')
        self.pg_data_path = pg_data_path
        self.backups_path = backups_path
        self.conf_path = conf_path
        self.sources_path = sources_path
        self.base_path = base_path
        self.conf_file_path = conf_file_path
        self.logfile = logfile
        self.container_logfile = os.path.join('/etc/odoo/', 'odoo.log')
        self.data_dir = data_dir

# Actions
    @api.multi
    def delete(self):
        _logger.info("Deleting Instance")
        if self.database_ids:
            raise Warning(_(
                'You can not delete an instance that has databases'))
        self.instance_repository_ids.write({'actual_commit': False})
        self.stop_odoo_service()
        self.stop_pg_service()
        self.delete_nginx_site()
        self.delete_paths()
        self.signal_workflow('sgn_cancel')

    @api.multi
    def create_instance(self):
        _logger.info("Creating Instance")
        self.make_paths()
        self.update_nginx_site()
        self.add_repositories()
        self.instance_repository_ids.repository_pull_clone_and_checkout(
            update=False)
        self.start_pg_service()
        self.update_conf_file()
        self.start_odoo_service()
        self.signal_workflow('sgn_to_active')

    @api.one
    def get_commands(self):

        pg_volume_links = (
            '-v %s:/var/lib/postgresql/data' % self.pg_data_path)
        odoo_port_links = (
            '-p 127.0.0.1:%i:8069 -p 127.0.0.1:%i:8072') % (
            self.xml_rpc_port, self.longpolling_port)
        odoo_volume_links = (
            '-v %s:/etc/odoo -v %s:/mnt/extra-addons -v %s:/var/lib/odoo -v %s:%s') % (
            self.conf_path, self.sources_path, self.data_dir,
            self.server_id.backups_path, self.server_id.backups_path)

        odoo_pg_link = '--link %s:db' % self.pg_container

        if self.service_type == 'docker':
            prefix = '--restart=always -d'
        else:
            # no usamos mas el --rm porque si no queda colgado al levantar
            # comoservicio
            prefix = '-d'

        # build images names
        odoo_image_name = '%s:%s' % (
            self.odoo_image_id.pull_name, self.odoo_image_tag_id.name)
        pg_image_name = '%s:%s' % (
            self.pg_image_id.pull_name, self.pg_image_tag_id.name)

        # build sufix
        odoo_sufix = self.odoo_sufix and ' %s' % self.odoo_sufix or ''
        odoo_sufix += self.module_load and ' --load=%s' % self.module_load or ''

        # odoo start commands
        self.start_odoo_cmd = 'docker run %s %s %s %s %s --name %s %s -- %s' % (
            prefix, self.odoo_image_id.prefix or '',
            odoo_port_links, odoo_volume_links, odoo_pg_link,
            self.odoo_container, odoo_image_name, odoo_sufix)

        self.start_attach_odoo_cmd = 'docker run %s %s %s %s %s --name %s %s %s' % (
            '-ti --rm -u root', self.odoo_image_id.prefix or '',
            odoo_port_links, odoo_volume_links, odoo_pg_link,
            self.odoo_container, odoo_image_name, '/bin/bash')

        user = 'odoo'
        if self.odoo_version in ('7.0'):
            user = 'openerp'

        self.start_attached_odoo_cmd = 'runuser -u %s openerp-server -- -c /etc/odoo/openerp-server.conf --logfile=False %s' % (
            user, odoo_sufix)

        # odoo command for update conf
        self.update_conf_cmd = 'docker run %s %s %s %s %s --name %s %s -- %s' % (
            '--rm', self.odoo_image_id.prefix or '',
            odoo_port_links, odoo_volume_links, odoo_pg_link,
            self.odoo_container, odoo_image_name,
            self.get_update_conf_command_sufix())

        # odoo update all command
        self.update_all_cmd = 'docker run %s %s %s %s %s --name %s %s -- %s' % (
            '--rm -ti', self.odoo_image_id.prefix or '',
            odoo_port_links, odoo_volume_links, odoo_pg_link,
            self.odoo_container, odoo_image_name,
            odoo_sufix + ' --stop-after-init --workers=0 -u all')

        # pg start command
        self.start_pg_cmd = 'docker run %s %s %s --name %s %s' % (
            prefix, self.pg_image_id.prefix or '', pg_volume_links,
            self.pg_container, pg_image_name)

        # kill commands
        self.kill_odoo_cmd = 'docker rm -f %s' % self.odoo_container
        self.kill_pg_cmd = 'docker rm -f %s' % self.pg_container

        # stop commands
        self.stop_odoo_cmd = 'docker stop %s' % self.odoo_container
        self.stop_pg_cmd = 'docker stop %s' % self.pg_container

        # restart commands
        self.restart_odoo_cmd = 'docker restart %s' % self.odoo_container
        self.restart_pg_cmd = 'docker restart %s' % self.pg_container

        # Logs
        self.odoo_log_cmd = 'tail -f %s' % self.logfile
        self.pg_log_cmd = 'docker logs -f %s' % self.pg_container

    @api.multi
    def get_tunnel_to_pg(self):
        self.ensure_one()
        server = self.server_id
        server.get_env()
        ip = sudo("docker inspect --format '{{ .NetworkSettings.IPAddress }}' %s" % self.pg_container)
        tunnel_to_pg = "ssh -L 5499:%s:5432 %s@%s -p %i" % (
            ip, server.user_name, server.main_hostname, server.ssh_port)
        raise Warning(_('Tunneling command to access postgres:\n%s\n\
            Password: %s\n\
            In your pgadmin you should enter:\n\
            *Host: localhost\n\
            *Port: 5499\n\
            *Usarname and pass: odoo') % (tunnel_to_pg, server.password))

    @api.multi
    def get_update_conf_command_sufix(self):
        self.ensure_one()
    # def update_conf_command(self):
    # def update_conf_command(self, force_no_workers=False):
        # Construimos commando
        # command = self.start_odoo_cmd
        command = ' --stop-after-init -s'

        if self.addons_path:
            command += ' --addons-path=' + self.addons_path
        # agregamos ' para que no de error con ciertos dominios
        command += ' --db-filter=' + "'%s'" % self.db_filter.rule
        command += ' --logfile=' + self.container_logfile
        command += ' --limit-time-real=' + str(self.limit_time_real)
        command += ' --limit-time-cpu=' + str(self.limit_time_cpu)
        command += ' --db_maxconn=' + str(self.db_maxconn)
        command += ' --without-demo=' + str(self.without_demo)
        # TODO only v8
        if self.odoo_version not in ('7.0'):
            command += ' --data-dir=/var/lib/odoo/'
        command += ' --workers=' + str(self.workers)
        # TODO ver si lo agregamos
        # command += ' --no-xmlrpcs'

        if self.module_load:
            command += ' --load=' + self.module_load

        if self.unaccent:
            command += ' --unaccent'

        if self.proxy_mode:
            command += ' --proxy-mode'

        # TODO only v8
        if self.logrotate and self.odoo_version not in ('7.0'):
            command += ' --logrotate'

        return command

    @api.multi
    def delete_paths(self):
        _logger.info("Deleting path and subpath of: %s " % self.base_path)
        self.environment_id.server_id.get_env()
        sudo('rm -r %s' % self.base_path, dont_raise=True)

    @api.multi
    def duplicate(self, environment, database_type, sufix, number):
        self.ensure_one()
        _logger.info('Duplicating Intance')
        new_instance = self.copy({
                'environment_id': environment.id,
                'database_type_id': database_type.id,
                'sufix': sufix,
                'number': number,
                })

        self.server_id.get_env()

        # make paths
        new_instance.make_paths()

        _logger.info('Coping pg data')
        fabtools.files.copy(
            self.pg_data_path, new_instance.pg_data_path,
            recursive=True, use_sudo=True)
        sudo('chown .docker -R ' + new_instance.pg_data_path)

        _logger.info('Coping data dir')
        fabtools.files.copy(
            self.data_dir, new_instance.data_dir,
            recursive=True, use_sudo=True)
        sudo('chmod 777 -R ' + new_instance.data_dir)

        _logger.info('Coping sources')
        fabtools.files.copy(
            self.sources_path, new_instance.sources_path,
            recursive=True, use_sudo=True)
        sudo('chmod 777 -R ' + new_instance.sources_path)

        _logger.info('Coping config')
        fabtools.files.copy(
            self.conf_path, new_instance.conf_path,
            recursive=True, use_sudo=True)
        sudo('chmod 777 -R ' + new_instance.conf_path)

        # Create new databases
        _logger.info('Duplicating surce instance database info')
        for database in self.database_ids:
            new_db = database.copy({
                'database_type_id': database_type.id,
                'instance_id': new_instance.id,
                })
            new_db.signal_workflow('sgn_to_active')
            # TODO ver si hace falta esto o no, el tema es que esa instancia no la terminamos activando
            # # we run this to deactivate backups
            # _logger.info('Renaiming database %s' % new_db.name)
            # new_db.rename_db('%s_%s' % (
            #     self.database_type_id.prefix, new_db.name))
            # new_db.config_backups()

        # return new instance view
        action = self.env['ir.model.data'].xmlid_to_object(
            'infrastructure.action_infrastructure_instance_instances')
        if not action:
            return False
        res = action.read()[0]
        # res['domain'] = [('id', 'in', databases.ids)]
        form_view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'infrastructure.view_infrastructure_instance_form')
        res['views'] = [(form_view_id, 'form')]
        res['res_id'] = new_instance.id
        return res

    @api.one
    def copy_databases_from(self, instance):
        if self.database_type_id.type == 'protected':
            raise Warning('You can not replace data in a instance of type\
                protected, you should do it manually or change type.')
        self.server_id.get_env()
        _logger.info('Copying database data from %s to %s' % (
            instance.name, self.name))
        # remove pg files and get new ones
        _logger.info('Removing pg data for %s' % self.name)
        fabtools.files.remove(
            self.pg_data_path, recursive=True, use_sudo=True)
        fabtools.files.copy(
            instance.pg_data_path, self.pg_data_path,
            recursive=True, use_sudo=True)

        # remove data files and get new ones
        _logger.info('Removing data dir data for %s' % self.name)
        fabtools.files.remove(
            self.data_dir, recursive=True, use_sudo=True)
        fabtools.files.copy(
            instance.data_dir, self.data_dir,
            recursive=True, use_sudo=True)

        # chown and chmod
        sudo('chown .docker -R ' + self.pg_data_path)
        sudo('chmod 777 -R ' + self.data_dir)

        # Restart services
        self.start_pg_service()
        self.start_odoo_service()

        # Unlink actual databases
        _logger.info('Unlinking actual databases records')
        for database in self.database_ids:
            database.signal_workflow('sgn_cancel')
            database.unlink()

        # Create new databases
        _logger.info('Duplicating surce instance database info')
        for database in instance.database_ids:
            new_db = database.copy({
                'database_type_id': self.database_type_id.id,
                'instance_id': self.id,
                })
            # we run this to deactivate backups
            new_db.signal_workflow('sgn_to_active')
            _logger.info('Renaiming database %s' % new_db.name)
            # we wait for service start
            # TODO mejorar esto, chequear que esta levantado en vez del slepp
            time.sleep(2)
            new_db.rename_db('%s_%s' % (
                self.database_type_id.prefix, new_db.name))
            new_db.config_backups()

    @api.one
    def databases_update_all(self):
        self.stop_odoo_service()
        for database in self.database_ids:
            sudo('%s -d %s' % (self.update_all_cmd, database.name))
        self.start_odoo_service()

    @api.multi
    def make_paths(self):
        """ Creamos todo los paths con 777 salvo el de posgreses que dejamos
        que se cree solo porque si no no anda por ser inseguro
        """
        _logger.info("Creating paths")
        self.environment_id.server_id.get_env()
        paths = [
            self.base_path,
            self.sources_path,
            self.conf_path,
            self.data_dir,
            self.backups_path,
            ]
        for path in paths:
            if exists(path, use_sudo=True):
                _logger.warning(("Folder '%s' already exists") % (path))
                continue
            _logger.info(("Creating path '%s'") % (path))
            sudo('mkdir -m 777 -p ' + path)

    @api.one
    def update_conf_file(self):
    # TODO implementar force no workers
    # def update_conf_file(self, force_no_workers=False):
        _logger.info("Updating conf file")
        self.environment_id.server_id.get_env()

        self.stop_odoo_service()

        if not exists(self.environment_id.path, use_sudo=True):
            raise except_orm(_('No Environment Path!'),
                             _("Environment path '%s' does not exists. \
                                Please create it first!")
                             % (self.environment_id.path))

        # Remove file if it already exists, we do it so we can put back some
        # booelan values as unaccent
        if exists(self.conf_file_path, use_sudo=True):
            # TODO hacer backup y si sale el except restaurar
            _logger.info("Remove old conf file")
            sudo('rm ' + self.conf_file_path)

        try:
            _logger.info("Running update conf command: '%s'" % self.update_conf_cmd)
            sudo(self.update_conf_cmd)
        except Exception, e:
            raise Warning(_("Can not create/update configuration file, this is what we get: \n %s") % (
                e))
        sed(
            self.conf_file_path,
            '(admin_passwd).*', 'admin_passwd = ' + self.admin_pass,
            use_sudo=True)

    @api.one
    def start_odoo_service(self):
        self.environment_id.server_id.get_env()
        # Fist stop
        self.stop_odoo_service()
        # Then Start
        _logger.info("Starting Odoo Service %s " % self.name)
        sudo(self.start_odoo_cmd)

    @api.one
    def restart_odoo_service(self):
        self.environment_id.server_id.get_env()
        _logger.info("Restarting Odoo Service %s " % self.name)
        sudo(self.restart_odoo_cmd)

    @api.one
    def stop_odoo_service(self):
        self.environment_id.server_id.get_env()
        _logger.info("Stopping Odoo Service %s " % self.name)
        try:
            sudo(self.stop_odoo_cmd)
        except:
            _logger.warning(("Could stop container '%s'") % (
                self.stop_odoo_cmd))
        try:
            sudo(self.kill_odoo_cmd)
        except:
            _logger.warning(("Could remove container '%s'") % (
                self.kill_odoo_cmd))

    @api.one
    def start_pg_service(self):
        self.environment_id.server_id.get_env()
        # Fist stop
        self.stop_pg_service()
        # Then Start
        _logger.info("Starting Postgresql Service %s" % self.name)
        sudo(self.start_pg_cmd)

    @api.one
    def restart_pg_service(self):
        self.environment_id.server_id.get_env()
        _logger.info("Restarting Postgresql Service %s" % self.name)
        sudo(self.restart_pg_cmd)

    @api.one
    def stop_pg_service(self):
        self.environment_id.server_id.get_env()
        _logger.info("Stopping Postgresql Service %s " % self.name)
        try:
            sudo(self.stop_pg_cmd)
        except:
            _logger.warning(("Could stop container '%s'") % (
                self.stop_pg_cmd))
        try:
            sudo(self.kill_pg_cmd)
        except:
            _logger.warning(("Could remove container '%s'") % (
                self.kill_pg_cmd))

    @api.one
    def delete_nginx_site(self):
        _logger.info("Deleting conf file")
        self.environment_id.server_id.get_env()
        nginx_sites_path = self.environment_id.server_id.nginx_sites_path
        nginx_site_file_path = os.path.join(
            nginx_sites_path,
            self.name
        )
        try:
            sudo('rm -f %s' % nginx_site_file_path)
        except Exception, e:
            _logger.warning(("Could remove nginx site file '%s', this is what we get: \n %s") % (
                self.service_file, e))

    @api.one
    def update_nginx_site(self):
        _logger.info("Updating nginx site")
        if not self.main_hostname:
            raise Warning(_('Can Not Configure Nginx if Main Site is not Seted!'))

        self.environment_id.server_id.get_env()

        server_names = [
            x.name for x in self.instance_host_ids if x.type != 'redirect_to_main']
        # TODO ver si dejamos esto o lo borramos, queremos que sea flexible desde el usuario
        # aunque vimos que preferentemente se va a configurar www como principal
        redirect_server_names = []
        # redirect_server_names = ['www.' + x for x in server_names]
        redirect_server_names += [
            x.name for x in self.instance_host_ids if x.type == 'redirect_to_main']

        if not server_names:
            raise Warning(_('You Must set at least one instance host!'))

        acces_log = os.path.join(
            self.environment_id.server_id.nginx_log_path,
            'access_' + re.sub('[-]', '_', self.name))
        error_log = os.path.join(
            self.environment_id.server_id.nginx_log_path,
            'error_' + re.sub('[-]', '_', self.name))
        xmlrpc_port = self.xml_rpc_port

        nginx_long_polling = ''

        if self.longpolling_port:
            nginx_long_polling = nginx_long_polling_template % (
                self.longpolling_port)
        # TODO modify template in order to give posibility to not use longpolling
        if self.type == 'secure':
            server_hostname_id = self.main_hostname_id.server_hostname_id
            if not self.main_hostname_id.server_hostname_id.ssl_available:
                raise Warning('To use Secure you nead a host with SSL enable.\
                    \nCustom certificate is not implemented yet!')
            nginx_site_file = nginx_ssl_site_template % (
                self.name,
                xmlrpc_port,
                self.name,
                self.longpolling_port,
                ' '.join(server_names),
                ' '.join(server_names),
                server_hostname_id.ssl_certificate_path,
                server_hostname_id.ssl_certificate_key_path,
                acces_log,
                error_log,
                self.name,
                self.name,
                self.name,
                )
        else:
            nginx_site_file = nginx_site_template % (
                ' '.join(server_names),
                acces_log,
                error_log,
                xmlrpc_port,
                nginx_long_polling
                )

        # Add redirections if exists
        if redirect_server_names:
            nginx_site_file = "%s\n%s" % (
                nginx_redirect_template % (
                    ' '.join(redirect_server_names),
                    self.main_hostname,
                    ),
                nginx_site_file,
                )

        # Check nginx sites-enabled directory exists
        nginx_sites_path = self.environment_id.server_id.nginx_sites_path
        if not exists(nginx_sites_path):
            raise Warning(
                _("Nginx '%s' directory not found! \
                Check if Nginx is installed!") % nginx_sites_path
            )

        # Check if file already exists and delete it
        nginx_site_file_path = os.path.join(
            nginx_sites_path,
            self.name
        )
        if exists(nginx_site_file_path, use_sudo=True):
            sudo('rm ' + nginx_site_file_path)

        # Create file
        append(nginx_site_file_path, nginx_site_file, use_sudo=True,)
        sudo('chmod 777 ' + nginx_site_file_path)

        # Restart nginx
        self.environment_id.server_id.reload_nginx()

    @api.multi
    def action_view_databases(self):
        '''
        This function returns an action that display a form or tree view
        '''
        self.ensure_one()
        databases = self.database_ids.search(
            [('instance_id', 'in', self.ids)])
        action = self.env['ir.model.data'].xmlid_to_object(
            'infrastructure.action_infrastructure_database_databases')

        if not action:
            return False
        res = action.read()[0]
        if len(self) == 1:
            res['context'] = {
                'default_instance_id': self.id,
                'search_default_instance_id': self.id,
                'search_default_not_cancel': 1,
                }
        if not len(databases.ids) > 1:
            form_view_id = self.env['ir.model.data'].xmlid_to_res_id(
                'infrastructure.view_infrastructure_database_form')
            res['views'] = [(form_view_id, 'form')]
            # if 1 then we send res_id, if 0 open a new form view
            res['res_id'] = databases and databases.ids[0] or False
        return res

# TODO llevar esto a un archivo y leerlo de alli
    # rewrite  ^/(.*)$  http://%s/$1 permanent;
nginx_redirect_template = """
server   {
    server_name %s;
    rewrite  ^/(.*)$  %s/$1 permanent;
}
"""
nginx_long_polling_template = """
    location /longpolling {
        proxy_pass   http://127.0.0.1:%i;
    }
"""
nginx_site_template = """
server {
    listen 80;
    server_name %s;
    access_log %s;
    error_log %s;

    location / {
            proxy_pass              http://127.0.0.1:%i;
            proxy_set_header        X-Forwarded-Host $host;
    }

%s

}
"""
nginx_ssl_site_template = """
upstream %s {
    server 127.0.0.1:%i weight=1 fail_timeout=300s;
}
upstream %s-im {
    server 127.0.0.1:%s weight=1 fail_timeout=300s;
}
server {
    listen 80;
    server_name %s;
    add_header Strict-Transport-Security max-age=2592000;
    rewrite ^/.*$ https://$host$request_uri? permanent;
}
server {
    listen 443;
    server_name %s;

    # ssl settings
    ssl on;
    ssl_certificate     %s;
    ssl_certificate_key %s;
    keepalive_timeout 60;

    # limit ciphers
    ssl_ciphers            HIGH:!ADH:!MD5;
    ssl_protocols            SSLv3 TLSv1;
    ssl_prefer_server_ciphers    on;

    # proxy header and settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
    proxy_redirect off;

    # Let the OpenERP web service know that we're using HTTPS, otherwise
    # it will generate URL using http:// and not https://
    proxy_set_header X-Forwarded-Proto https;

    # odoo log files
    access_log %s;
    error_log  %s;

    # increase proxy buffer size
    proxy_buffers 16 64k;
    proxy_buffer_size 128k;

    # force timeouts if the backend dies
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;

    # enable data compression
    gzip on;
    gzip_min_length 1100;
    gzip_buffers 4 32k;
    gzip_types text/plain application/x-javascript text/xml text/css;
    gzip_vary on;

    # cache some static data in memory for 60mins.
    # under heavy load this should relieve stress on the OpenERP web interface a bit.
    location ~* /web/static/ {
        proxy_cache_valid 200 60m;
        proxy_buffering    on;
        expires 864000;
        proxy_pass http://%s;
    }

    location / {
        proxy_pass http://%s;
    }

    location /longpolling {
        proxy_pass http://%s-im;
    }
}
"""
# odoo_upstar = template_upstar_file % ()
template_upstar_file = """
description "%s Container"
author "ADHOC SA"

start on filesystem and started docker %s
stop on runlevel [!2345]

# The process wil be restarted if ended unexpectedly
respawn

# If the process is respawned more than 10 times within an interval of 90 timeout seconds, the process will be stopped automatically, and not $
respawn limit 10 90

script
  /usr/bin/docker %s
end script
post-stop script
  /usr/bin/docker %s
end script
"""

# TODO llevar esto a un archivo y leerlo de alli
template_service_file = """
#!/bin/sh

### BEGIN INIT INFO
# Provides:             openerp-server
# Required-Start:       $remote_fs $syslog
# Required-Stop:        $remote_fs $syslog
# Should-Start:         $network
# Should-Stop:          $network
# Default-Start:        2 3 4 5
# Default-Stop:         0 1 6
# Short-Description:    Enterprise Resource Management software
# Description:          odoo is a complete ERP and CRM software.
### END INIT INFO

# EDITABLE
USER=%s
CONFIG=%s
DAEMON=%s

# NO TOCAR
PATH=/sbin:/bin:/usr/sbin:/usr/bin
NAME=odoo-$USER
DESC=odoo-$USER

test -x ${DAEMON} || exit 0

set -e

case "${1}" in
        start)
                echo -n "Starting ${DESC}: "
        sleep 5

                start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
                        --chuid ${USER} --background --make-pidfile \
            --exec ${DAEMON} -- --config=${CONFIG}  \


                echo "${NAME}."
                ;;

        stop)
                echo -n "Stopping ${DESC}: "

                start-stop-daemon --stop --quiet --pidfile /var/run/${NAME}.pid \
                        --oknodo

                echo "${NAME}."
                ;;

        restart|force-reload)
                echo -n "Restarting ${DESC}: "

                start-stop-daemon --stop --quiet --pidfile /var/run/${NAME}.pid \
                        --oknodo

                sleep 1

                start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
                        --chuid ${USER} --background --make-pidfile \
            --exec ${DAEMON} -- --config=${CONFIG}  \


                echo "${NAME}."
                ;;

        restart-with-update)
                start-stop-daemon --stop --quiet --pidfile /var/run/${NAME}.pid \
                        --oknodo

                sleep 1

                if [ -z ${2} ]
                then
                    echo -n "Restarting ${DESC}: "
                    start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
                        --chuid ${USER} --background --make-pidfile \
            --exec ${DAEMON} -- --config=${CONFIG}  \
                else
                    if [ -z ${3} ]
                    then
                        echo -n "Restarting with update ${DESC} all modules on database ${2}: "
                        start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
                                --chuid ${USER} --background --make-pidfile \
                --exec ${DAEMON} -- --config=${CONFIG}  \
                                    --update=all -d ${2}
                    else
                        echo -n "Restarting with update ${DESC} modules ${3} on database ${2}: "
                        start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
                                --chuid ${USER} --background --make-pidfile \
                --exec ${DAEMON} -- --config=${CONFIG}  \
                                    --update=${3} -d ${2}
                    fi
                fi

                echo "${NAME}."
                ;;

        *)

                N=/etc/init.d/${NAME}
                echo "Usage: ${NAME} {start|stop|restart|force-reload|restart-with-update [database [modules]]}" >&2
                exit 1
                ;;

esac

exit 0
"""
