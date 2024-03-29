# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "education_fees"
app_title = "Education Fees"
app_publisher = "Sayed Hameed Ebrahim"
app_description = "Generate education fees"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "sayed.saar@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/education_fees/css/education_fees.css"
# app_include_js = "/assets/education_fees/js/education_fees.js"

# include js, css files in header of web template
# web_include_css = "/assets/education_fees/css/education_fees.css"
# web_include_js = "/assets/education_fees/js/education_fees.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "education_fees.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "education_fees.install.before_install"
# after_install = "education_fees.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "education_fees.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"education_fees.tasks.all"
# 	],
# 	"daily": [
# 		"education_fees.tasks.daily"
# 	],
# 	"hourly": [
# 		"education_fees.tasks.hourly"
# 	],
# 	"weekly": [
# 		"education_fees.tasks.weekly"
# 	]
# 	"monthly": [
# 		"education_fees.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "education_fees.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "education_fees.event.get_events"
# }

fixtures = [
	{"dt": "DocType", "filters": [
		["name", "in", [
				"Fee Schedule Student",
				"Student Fee Structure",
				"Student Fee Component",
        "Student Fee Schedule"
			]
		]
	]},
	{"dt": "Custom Field", "filters": [
		["name", "in", [
				"Student-category",
				"Student-transportation",
				"Fees-student_fee_structure",
        "Fees-student_fee_schedule",
        "Fees-fee_components"
			]
		]
	]}
]
