# -*- coding: utf-8 -*-

{
    'name': u'Infrastructure',
    'version': '0.2.0',
    'description': u'Infrastructure Management',
    'category': u'base.module_category_knowledge_management',
    'author': u'Ingeniería Adhoc',
    'website': 'www.ingadhoc.com',
    'license': 'AGPL-3',
    'depends': [u'mail'],
    'data': [
        u'wizard/duplicate_db_wizard_view.xml',
        u'wizard/restore_database_wizard_view.xml',
        u'security/infrastructure_group.xml',
        u'view/infrastructure_menuitem.xml',
        u'view/server_hostname_view.xml',
        u'view/instance_host_view.xml',
        u'view/server_repository_view.xml',
        u'view/partner_view.xml',
        u'view/mailserver_view.xml',
        u'view/repository_view.xml',
        u'view/service_view.xml',
        u'view/environment_version_view.xml',
        u'view/environment_repository_view.xml',
        u'view/database_view.xml',
        u'view/db_backup_policy_view.xml',
        u'view/db_filter_view.xml',
        u'view/instance_view.xml',
        u'view/service_command_view.xml',
        u'view/repository_branch_view.xml',
        u'view/server_configuration_view.xml',
        u'view/server_change_view.xml',
        u'view/server_service_view.xml',
        u'view/database_type_view.xml',
        u'view/command_view.xml',
        u'view/server_configuration_command_view.xml',
        u'view/environment_view.xml',
        u'view/server_view.xml',
        u'view/database_backup_view.xml',
        u'data/cron.xml',
        u'data/database_track.xml',
        u'data/db_backup_policy.xml',
        u'data/environment_track.xml',
        u'data/instance_track.xml',
        u'data/server_track.xml',
        u'workflow/database_workflow.xml',
        u'workflow/environment_workflow.xml',
        u'workflow/instance_workflow.xml',
        u'workflow/server_workflow.xml',
        u'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'demo': [
        u'data/demo/res.partner.csv',
        u'data/demo/infrastructure.repository_branch.csv',
        u'data/demo/infrastructure.repository.csv',
        u'data/demo/infrastructure.server_configuration.csv',
        u'data/demo/infrastructure.server.csv',
        u'data/demo/infrastructure.server_hostname.csv',
        u'data/demo/infrastructure.environment_version.csv',
        u'data/demo/infrastructure.environment.csv',
        u'data/demo/infrastructure.db_filter.csv',
        u'data/demo/infrastructure.database_type.csv',
        u'data/demo/infrastructure.server_repository.csv',
        u'data/demo/infrastructure.instance.csv',
        u'data/demo/infrastructure.instance_host.csv',
        u'data/demo/infrastructure.server_configuration_command.csv',
        u'data/demo/infrastructure.database.csv'
        ],
    }
