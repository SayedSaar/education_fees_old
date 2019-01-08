# -*- coding: utf-8 -*-
# Copyright (c) 2018, Sayed Hameed Ebrahim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import money_in_words
from frappe.utils import cint, flt, cstr
from frappe.utils.background_jobs import enqueue
from frappe import _

class StudentFeeSchedule(Document):
	def onload(self):
		info = self.get_dashboard_info()
		self.set_onload('dashboard_info', info)

	def get_dashboard_info(self):
		info = {
			"total_paid": 0,
			"total_unpaid": 0,
			"currency": erpnext.get_company_currency(self.company)
		}

		fees_amount = frappe.db.sql("""select sum(grand_total), sum(outstanding_amount) from `tabFees`
			where student_fee_schedule=%s and docstatus=1""", (self.name))

		if fees_amount:
			info["total_paid"] = flt(fees_amount[0][0]) - flt(fees_amount[0][1])
			info["total_unpaid"] = flt(fees_amount[0][1])

		return info

	def validate(self):
		self.calculate_total_and_program()

	def after_save(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('utf-8')

		academic_term = self.academic_term
		academic_year = self.academic_year

		conditions = ""
		if academic_term:
			conditions += " and fees.academic_term='{}'".format(frappe.db.escape(academic_term))

		due_month = frappe.utils.formatdate(self.due_date, 'MM')

		if self.due_date:
			conditions += " and month(fees.due_date)={}".format(frappe.db.escape(due_month))

		msg = ""

		for student in self.fee_schedule_student:
			student_condition = ""
			if student:
				student_condition = "  and fees.student={}".format(frappe.db.escape(student.student))

			student_fees = frappe.db.sql("""
				select sfc.fees_category, fees.student_name, fees.student
					from `tabStudent Fee Component` sfc, `tabFees` fees
					where
						sfc.parent = fees.name
						and fees.docstatus = 1
						and fees.academic_year = %s 
						{conditions}
						{student_condition}
				""".format(conditions=conditions, student_condition=student_condition), (academic_year), as_dict=1)

			if len(student_fees):
				msg += "<br><b>The following fees has already been generated for student (" + student_fees[0].student_name + ") For month (" + due_month + "):</b><br>"
				for fee in student_fees:
					msg += "- " + fee.fees_category + "<br>"
		
		if msg:
			frappe.msgprint(msg)

	def calculate_total_and_program(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('utf-8')

		no_of_students = 0
		for d in self.student_groups:
			# if not d.total_students:
			d.total_students = get_total_students(d.student_group, self.academic_year, self.student_fee_structure, 
				self.academic_term)
			no_of_students += cint(d.total_students)

			# validate the program of fee structure and student groups
			student_group_program = frappe.db.get_value("Student Group", d.student_group, "program")
			if self.program and student_group_program and self.program != student_group_program:
				frappe.msgprint(_("Program in the Fee Structure and Student Group {0} are different.")
					.format(d.student_group))
		#self.grand_total = no_of_students*self.total_amount
		#self.grand_total_in_words = money_in_words(self.grand_total)

	def create_fees(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('utf-8')

		self.db_set("fee_creation_status", "In Process")
		frappe.publish_realtime("fee_schedule_progress",
			{"progress": "0", "reload": 1}, user=frappe.session.user)

		total_records = sum([int(d.total_students) for d in self.student_groups])
		if total_records > 10:
			frappe.msgprint(_('''Fee records will be created in the background.
				In case of any error the error message will be updated in the Schedule.'''))
			enqueue(generate_fee, queue='default', timeout=6000, event='generate_fee',
				student_fee_schedule=self.name)
		else:
			generate_fee(self.name)

	def get_fee_schedule_students(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('utf-8')

		academic_year = self.get("academic_year")
		academic_term = self.get("academic_term")
		student_groups = self.get("student_groups")

		student_fee_structure = self.get("student_fee_structure")
		fee_structure_doc = frappe.get_doc("Student Fee Structure", student_fee_structure)

		student_category_fees = {}
		student_category_fees["other"] = 0

		transport_fees = {}
		transport_fees["other"] = 0
		
		for component in fee_structure_doc.components:
			if component.student_category and not component.is_transport:
				if student_category_fees.has_key(component.student_category):
					student_category_fees[component.student_category] += flt(component.amount)
				else:
					student_category_fees[component.student_category] = flt(component.amount)
			elif not component.is_transport and not component.student_category:
				student_category_fees["other"] += component.amount
			elif component.student_category and component.is_transport:
				if transport_fees.has_key(component.student_category):
					transport_fees[component.student_category] += flt(component.amount)
				else:
					transport_fees[component.student_category] = flt(component.amount)
			elif not component.student_category and component.is_transport:
				transport_fees["other"] += component.amount

		if transport_fees["other"] > 0:
			for key, value in transport_fees.iteritems():
				if key != "other":
					transport_fees[key] += flt(transport_fees["other"])
		
		if student_category_fees["other"] > 0:
			for key, value in student_category_fees.iteritems():
				if key != "other":
					student_category_fees[key] += flt(student_category_fees["other"])

		#frappe.msgprint(str(student_category_fees))
		#frappe.msgprint(str(transport_fees))
		
		#frappe.msgprint(str(len(student_groups)))

		if len(student_groups) > 0:
			for student_group in student_groups:
				if student_group.student_group:
					students = get_students(academic_year, student_group.student_group, student_fee_structure, academic_term)

					for student in students:
						exist = False
						for i in self.get("fee_schedule_student"):
							if student.student == i.student:
								exist = True
						if exist == False:
							#frappe.throw(str(students))
							student_row = self.append("fee_schedule_student")
							student_row.student = student.student
							student_row.student_name = student.student_name
							if student.category and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
								student_row.amount = flt(student_category_fees[student.category]) + flt(transport_fees["other"] if len(transport_fees) == 1 else transport_fees[student_category] )
							elif not student.category and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
								student_row.amount = flt(student_category_fees["other"]) + flt(transport_fees["other"])
							elif student.category and not(student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
								student_row.amount = flt(student_category_fees[student.category])
							elif not student.category:
								student_row.amount = flt(student_category_fees["other"])
							
		else: 
			students = get_students(academic_year, None, student_fee_structure, academic_term)
			for student in students:
				exist = False
				for i in self.get("fee_schedule_student"):
					if student.student == i.student:
						exist = True
				if exist == False:
					#frappe.throw(str(students))
					student_row = self.append("fee_schedule_student")
					student_row.student = student.student
					student_row.student_name = student.student_name
						
					if student.category and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
						student_row.amount = flt(student_category_fees[student.category]) + flt(transport_fees["other"] if len(transport_fees) == 1 else transport_fees[student_category] )
					elif not student.category and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
						frappe.msgprint(str(student.transportation))
						student_row.amount = flt(student_category_fees["other"]) + flt(transport_fees["other"])
					elif student.category and not(student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
						student_row.amount = flt(student_category_fees[student.category])
					elif not student.category:
						student_row.amount = flt(student_category_fees["other"])

def generate_fee(student_fee_schedule):
	import sys
	reload(sys)
	sys.setdefaultencoding('utf-8')

	doc = frappe.get_doc("Student Fee Schedule", student_fee_schedule)
	error = False
	total_records = len(doc.fee_schedule_student)
	#frappe.throw(str(total_records))
	created_records = 0

	if not total_records:
		frappe.throw(_("Please setup Students under Student Groups"))

	academic_year = doc.academic_year
	academic_term = doc.academic_term

	students_list = ""
	for student in doc.fee_schedule_student:
		students_list += "'" + student.student + "',"

	students_list = students_list[:-1]

	conditions = ""
	if academic_term:
		conditions += " and pe.academic_term='{}'".format(frappe.db.escape(academic_term))

	students = frappe.db.sql("""
		select pe.student, pe.student_name, pe.program, pe.student_batch_name, stu.category, stu.transportation, pe.name `program_enrollment`
			from `tabStudent Group Student` sgs, `tabProgram Enrollment` pe, `tabStudent` stu
			where
				stu.name = pe.student 
				and	pe.student = sgs.student
				and pe.academic_year = %s 
				and sgs.active = 1 
				and pe.student in ({studentslist})
				{conditions}
		""".format(conditions=conditions, studentslist=students_list), (academic_year), as_dict=1)

	generated_fees = []

	for student in students:
		if student.student not in generated_fees:
			generated_fees.append(student.student)
			#student_doc = frappe.get_doc("Student", student)
			import sys
			try:
				fees_doc = get_mapped_doc("Student Fee Schedule", student_fee_schedule,	{
					"Student Fee Schedule": {
						"doctype": "Fees",
						"field_map": {
							"name": "Student Fee Schedule"
						}
					}
				})
				fees_doc.student = student.student
				fees_doc.student_name = student.student_name
				fees_doc.program = student.program
				fees_doc.program_enrollment = student.program_enrollment
				fees_doc.student_batch = student.student_batch_name
				fees_doc.send_payment_request = doc.send_email
				fees_doc.student_fee_schedule = student_fee_schedule
				#fees_doc.student_fee_structure = doc.student_fee_structure
				fees_doc.student_category = student.category
				#Components
				total_amount = 0
				
				for component in doc.components:
					if component.student_category and component.student_category == student.category and not component.is_transport:
						component_row = fees_doc.append("fee_components")
						component_row.student_category = component.student_category
						component_row.amount = component.amount
						component_row.fees_category = component.fees_category
						component_row.is_transport = component.is_transport
						total_amount += component.amount
					elif component.student_category and component.student_category == student.category and component.is_transport and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
						component_row = fees_doc.append("fee_components")
						component_row.student_category = component.student_category
						component_row.amount = component.amount
						component_row.fees_category = component.fees_category
						component_row.is_transport = component.is_transport
						total_amount += component.amount
					elif not component.student_category and component.is_transport and (student.transportation == "School Bus" or student.transportation == "باص المدرسة"):
						component_row = fees_doc.append("fee_components")
						component_row.student_category = component.student_category
						component_row.amount = component.amount
						component_row.fees_category = component.fees_category
						component_row.is_transport = component.is_transport
						total_amount += component.amount
					elif not component.student_category and not component.is_transport:
						component_row = fees_doc.append("fee_components")
						component_row.student_category = component.student_category
						component_row.amount = component.amount
						component_row.fees_category = component.fees_category
						component_row.is_transport = component.is_transport
						total_amount += component.amount
				
				#fees_doc.fee_components = fee_components
				#Total
				fees_doc.grand_total = total_amount
				fees_doc.outstanding_amount = total_amount
				fees_doc.grand_total_in_words = money_in_words(total_amount)			
				fees_doc.save()
				fees_doc.submit()
				created_records += 1
				frappe.publish_realtime("fee_schedule_progress", {"progress": str(int(created_records * 100/total_records))}, user=frappe.session.user)

			except Exception as e:
				error = True
				err_msg = frappe.local.message_log and "\n\n".join(frappe.local.message_log) or cstr(e)
				frappe.msgprint('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

	if error:
		frappe.db.rollback()
		frappe.db.set_value("Student Fee Schedule", student_fee_schedule, "fee_creation_status", "Failed")
		frappe.db.set_value("Student Fee Schedule", student_fee_schedule, "error_log", err_msg)

	else:
		frappe.db.set_value("Student Fee Schedule", student_fee_schedule, "fee_creation_status", "Successful")
		frappe.db.set_value("Student Fee Schedule", student_fee_schedule, "error_log", None)

	frappe.publish_realtime("fee_schedule_progress",
		{"progress": "100", "reload": 1}, user=frappe.session.user)


def get_students(academic_year, student_group=None, student_fee_structure=None, academic_term=None):
	import sys
	reload(sys)
	sys.setdefaultencoding('utf-8')

	fee_structure_doc = frappe.get_doc("Student Fee Structure", student_fee_structure)
	
	students = []

	for component in fee_structure_doc.components:
		student_category = component.student_category
		 
		conditions = ""
		if student_category:
			conditions = conditions + " and stu.category='{}'".format(frappe.db.escape(student_category))
		if academic_term:
			conditions = conditions + " and pe.academic_term='{}'".format(frappe.db.escape(academic_term))
		if student_group:
			conditions = conditions + " and sgs.parent='{}'".format(frappe.db.escape(student_group))
	
		#frappe.throw("""
                #        select pe.student, pe.student_name, pe.program, pe.student_batch_name, stu.category, stu.transportation
                #        from `tabStudent Group Student` sgs, `tabProgram Enrollment` pe, `tabStudent` stu
                #        where
                #                stu.name = pe.student 
                #                and     pe.student = sgs.student 
                #                and pe.academic_year = {academic_year}
                #                and sgs.active = 1
                #                {conditions}
                #        """.format(conditions=conditions,academic_year=academic_year))	
		students_list = frappe.db.sql("""
			select pe.student, pe.student_name, pe.program, pe.student_batch_name, stu.category, stu.transportation
			from `tabStudent Group Student` sgs, `tabProgram Enrollment` pe, `tabStudent` stu
			where
				stu.name = pe.student 
				and	pe.student = sgs.student 
				and pe.academic_year = %s
				and sgs.active = 1
				{conditions}
			""".format(conditions=conditions), (academic_year), as_dict=1)



		for student in students_list:
			if student not in students:
				students.append(student)
		
	return students


@frappe.whitelist()
def get_total_students(academic_year, student_group, student_fee_structure=None, academic_term=None):
	total_students = get_students(academic_year, student_group, student_fee_structure, academic_term)
	return len(total_students)


@frappe.whitelist()
def get_fee_structure(source_name,target_doc=None):
	fee_request = get_mapped_doc("Student Fee Structure", source_name,
		{"Student Fee Structure": {
			"doctype": "Student Fee Schedule"
		}}, ignore_permissions=True)
	return fee_request
