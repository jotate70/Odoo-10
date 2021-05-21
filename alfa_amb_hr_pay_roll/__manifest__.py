# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Alfa amb hr pay roll',
    'version': '1.0',
    'website': 'hhttp://www.alfaam.com.co',
    'category': 'Alfa Amb',
    'summary': 'Alfa amb hr pay roll',
    'author': 'ALFA AMB',
    'description': """
        Esta aplicacion genera adaptacion de la funcionalidad el modulo de nomina y empleados para ajustarse 
        a las necesidades Colombianas. 
        En particular, en el modelo hr.contract genera los campos de EPS, AFP. CESANTIAS, ARL, REISGO ARL, 
        tambien crea el modelo de NIVELES ARL para poder ser asociados a cada contrato, con un nivel porcentaje 
        de riesgo configurable.
        Tambien crea el flujo de gestion de novedades, que se encarga de recibir las diferentes novedades 
        de nomina de cada mes, y gestionar la cadena de su aprobacion y confirmacion, de modo que, 
        una vez aprobadas las novedades, se cargan automaticamente en los inputs de las reglas de nomina, y una vez confirmada la nomina, estas novedades pasan a estado confirmado.
        Tambien se crean las reglas generales de calculo de nomina de acuerdo al Codigo Sustantivo de Trabajo Colombiano.
        Se modifica el informe de nomina con los campos necesarios, asi como se automatiza el envio masivo de 
        los comprobantes al correo de cada empleado.
	""",
    'depends': [
        'hr_payroll',
        'hr_payroll_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/hr_payroll_report.xml',
        'report/report_payslip_templates.xml',
        'wizard/hr_payroll_payslips_by_employees_views.xml',
        'views/alfa_amb_multi_confirm_hr_payslip.xml',
        'views/alfa_amb_multi_cancel_hr_payslip..xml',
        'views/alfa_amb_multi_draft_hr_payslip..xml',
        'views/alfa_amb_multi_recalculate_hr_payslip.xml',
        'views/alfa_amb_multi_print_hr_payslip.xml',
        'views/alfa_amb_multi_print_hr_payslip_run.xml',
        'views/alfa_amb_approved_novelty.xml',
        'views/alfa_amb_risk_classes.xml',
        'views/alfa_amb_hr_pay_roll_configuration.xml',
        'views/alfa_amb_hr_payslip_configuration.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_contribution_register.xml',
        'views/alfa_amb_hr_novelty.xml',
        'views/alfa_amb_hr_novelty_retefuente.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_run.xml',
        'views/hr_salary_rule.xml',
        'views/hr_payslip_line.xml',
        'views/menus.xml',
        'data/alfa_amb_risk_classes_data.xml',
        'data/alfa_amb_risk_classes_precision.xml',
        'data/hr_contribution_register_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_rule_input.xml',
        'data/hr_payroll_structure_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
