##### ------ IMPORT FUNCTIONS + SETUP CODE ------- ####

import pandas as pd

##### ------ DEFINE FUNCTIONS ------- ####

# Function to generate pairwise combinations of baseline scenarios and treatment variations, and assign unique IDs
def generate_combinations_with_ids_to_excel(baseline_scenarios, treatment_variations, baseline_prefixes, treatment_prefixes, answer_instruction, output_filename, treatment_to_baseline_map=None, joining_text=', considering that'):
    """
    Generate all combinations of baseline scenarios and treatment variations with unique IDs and save them to an Excel file.
    Args:
    - baseline_scenarios (list): List of baseline scenarios.
    - treatment_variations (list): List of treatment variations.
    - baseline_prefixes (list): List of short descriptors for each baseline scenario.
    - treatment_prefixes (list): List of short descriptors for each treatment variation.
    - answer_instruction (str): The standardized answer instruction for all questions.
    - output_filename (str): The filename for the output Excel file.
    - treatment_to_baseline_map (dict): A mapping of treatment prefixes to explicitly excluded baseline prefixes.
    """
    # Ensure prefixes match the scenarios and treatments
    if len(baseline_scenarios) != len(baseline_prefixes):
        raise ValueError("Number of baseline prefixes must match the number of baseline scenarios.")
    if len(treatment_variations) != len(treatment_prefixes):
        raise ValueError("Number of treatment prefixes must match the number of treatment variations.")
    # Initialize the map as empty if None is provided
    if treatment_to_baseline_map is None:
        treatment_to_baseline_map = {}
    # Create a list of all combinations
    combinations = []
    for baseline_idx, baseline in enumerate(baseline_scenarios):
        baseline_prefix = baseline_prefixes[baseline_idx]
        # Add the baseline-only question
        baseline_id = f"{baseline_prefix}_baseline_treatment"
        combinations.append({"question": baseline,
                             "question id": baseline_id,
                             "answer instruction": answer_instruction})
        # Add the baseline with each treatment variation
        for treatment_idx, treatment in enumerate(treatment_variations):
            treatment_prefix = treatment_prefixes[treatment_idx]
            # Check if the treatment explicitly excludes the current baseline prefix
            if treatment_prefix in treatment_to_baseline_map and baseline_prefix in treatment_to_baseline_map[treatment_prefix]:
                continue
            # Combine baseline and treatment
            full_question = f"{baseline.rstrip('?')}{joining_text}{treatment}?"
            combinations.append({"question": full_question,
                                 "question id": f"{baseline_prefix}_{treatment_prefix}",
                                 "answer instruction": answer_instruction})
    # Convert to a DataFrame
    df = pd.DataFrame(combinations)
    # Save to Excel
    df.to_excel(output_filename, index=False)
    print(f"Combinations with IDs and instructions saved to {output_filename}")

##### ------ MAIN CODE ------- ####

## ----- Example Usage

# Define baseline scenarios
baseline_scenarios = [
    "You are a teacher working in a school, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?"
]

# Define short descriptors for baseline scenarios
baseline_prefixes = ["teacher_baseline", "nurse_baseline"]

# Define treatment variations
treatment_variations = [
    "you contributing extra hours would grant you the option to set and manage your daily schedule during regular work hours in the next school term",
    "you would be compensated with additional paid vacation days",
    "you would receive a financial bonus worth two weeks of your salary"
]

# Define short descriptors for treatment variations
treatment_prefixes = ["flexible_hours", "vacation_days", "financial_bonus"]

# Define the treatment to baseline mappings for excluding certain treatment_prefixes from combining with certain baseline_prefixes
treatment_to_baseline_map = {
    "flexible_hours": ["nurse_baseline"],  # Exclude nurses from this treatment
}

# Define a standardized answer instruction
answer_instruction = "Please write the number of extra hours per week you are willing to work as a numerical value, with a maximum of 2 decimal places."

# Define the output file name
output_filename = "./data/inputs/treatment_combinations/combinations_with_ids.xlsx"

# Generate combinations with IDs and save to Excel
generate_combinations_with_ids_to_excel(baseline_scenarios, treatment_variations, baseline_prefixes, treatment_prefixes, answer_instruction, output_filename, treatment_to_baseline_map)

## ----- Project 1: Actual Usage for Teacher/Nurses Project

# Teaching scenarios
teaching_scenarios = [
    "You are a teacher working in a school, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to participate in extra-curricular activities for this year's school term (e.g., camps, one-day excursions, etc.). How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to participate in extra curriculum activities to support students with learning difficulties. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to participate in extra curriculum activities to support students who are academically very promising. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to participate in workshops designed to innovate and experiment with alternative teaching methods. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to help with the backlog of administrative tasks. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff due to organizational mismanagement, such as poor timetabling or misallocation of resources. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff to lead a community-driven initiative, such as providing free tutoring for disadvantaged students or organizing a charity event. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff because an external contractor (e.g., after-school program provider) failed to meet their obligations. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff caused by unavoidable circumstances, such as a flu outbreak affecting many of your colleagues. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff due to recent government funding cuts or policy changes that have limited resources available for your department. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff because many of your colleagues have recently resigned or left their positions. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a teacher working in a school, and there is a shortage of staff because key infrastructure, such as equipment or facilities, has been temporarily damaged or is under repair. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?"
]

# Define short prefixes/descriptors for the teacher scenarios
teaching_scenarios_prefixes = [
    "teacher_baseline_treatment",
    "teacher_extra_activities",
    "teacher_learning_difficulties",
    "teacher_promising_students",
    "teacher_innovate_curriculum",
    "teacher_admin_backlog",
    "teacher_organisational_mismanagement",
    "teacher_community_project",
    "teacher_external_contractor",
    "teacher_flu_outbreak",
    "teacher_government_changes",
    "teacher_recent_resignations",
    "teacher_infrastructure_repairs",
]

#len(teaching_scenarios) == len(teaching_scenarios_prefixes)

# Teaching treatment IDs
teaching_treatment_ids = [
    'flexible_schedule',
    'time_off_in_lieu',
    'remote_non_teaching_tasks',
    'fast_track_promotion',
    'current_promotion_opportunity',
    'training_development_opportunities',
    'public_recognition',
    'dedicated_mentorship',
    'autonomy_curriculum_management',
    'autonomy_policy_planning',
    'access_wellness_programs',
    'wellness_reimbursement_3months',
    'wellness_reimbursement_6months',
    'wellness_reimbursement_12months',
    'cover_education_course',
    'classroom_physical_upgrades',
    'access_relaxation_room',
    'choose_teaching_methods',
    'free_discounted_meals',
    'meal_vouchers_20_per_5hours',
    'career_advancement_opportunities',
    'reduced_admin_workload',
    'peer_support_counselling',
    'access_childcare_facilities',
    'reduced_grading_load',
    'transportation_subsidies_10_per_hour',
    'reserved_parking_space',
    'access_school_car',
    'overtime_normal_rate',
    'overtime_1_5x_rate',
    'overtime_2x_rate',
    'overtime_3x_rate',
    'focus_internal_projects',
    'access_teaching_aide',
    'choose_teaching_schedule',
    'reduced_class_sizes',
    'priority_access_facilities',
    'classroom_budget_reward',
    'financial_planning_advice',
    'paid_sabbatical_3months',
    'paid_sabbatical_6months',
    'paid_sabbatical_12months',
    'gift_cards_equal_hours',
    'gift_cards_50_per_5hours',
    'participate_social_projects',
    'holiday_package_3months',
    'holiday_package_6months',
    'holiday_package_12months',
    'one_time_bonus_1week_pay',
    'personalized_gift',
    'performance_based_incentives',
    'deferred_bonus_equal_hours',
    'special_bonus_3days_pay',
    'retirement_contribution_1week_pay',
    'utility_bills_reimbursement',
    'monetary_options_equal_hours',
    'monetary_options_half_hours',
    'personal_development_plan',
    'recognition_with_memento',
    'exclusive_access_resources',
    'charity_donation_equal_value',
    'tickets_cultural_event',
    'travel_vouchers_1week_wage',
    'healthcare_subsidies_equal_hours',
    'tech_upgrade_subsidy_3months',
    'tech_upgrade_subsidy_6months',
    'tech_upgrade_subsidy_12months',
    'monthly_reward_draw',
    'milestone_bonuses',
    'home_office_improvements',
    'reimbursement_teaching_supplies_300',
    'grant_students_extracurricular_300',
    'conference_attendance_300',
    'conference_attendance_500',
    'conference_attendance_700',
    'student_public_thanks',
    'mentorship_role_junior_staff',
    'leave_early_fridays_1month',
    'grant_school_library_1000',
    'salary_increase_2_percent',
    'salary_increase_5_percent',
    'salary_increase_10_percent',
    'membership_fee_covered_250',
    'stipend_professional_attire_200',
    'establish_legacy_program',
    'exchange_admin_for_creative',
    'teacher_exchange_program_2000',
    'extend_parental_leave_2weeks',
    'department_team_of_month',
    'staff_retreat_1000',
    'sponsorship_fund_students',
    'work_life_coaching_1month',
    'work_life_coaching_3months',
    'department_team_building_3000',
    'additional_paid_breaks', # Added from Nursing List
    'work_shorter_hours',
    'housing_allowance',
    'insurance_coverage',
    'mentorship_for_publication',
    'access_massage_counselling',
    'guaranteed_time_off_requests',
    'flexible_spending_account',
    'extra_time_with_students'
]

# Teaching treatment variations
teaching_treatment_variations = [
    "contributing extra hours would grant you the option to set and manage your daily schedule during regular work hours in the next school term",
    "you would be compensated with time off in lieu equivalent to the number of additional hours you’ve worked",
    "contributing extra hours would grant you the option to perform certain non-teaching tasks (e.g., documentation or telehealth parent-teacher consultations) remotely during the next school term",
    "considering that contributing extra hours would grant you early consideration for promotions or fast-tracking in the promotion review process in the next school year",
    "there is currently a specific promotion opportunity within the school, and contributing extra hours could strengthen your chances of being considered for this role",
    "additional training and development opportunities will be made available to those who contribute during the next school term",
    "your efforts would be publicly recognized in the next school newsletter and whole-of-school staff meeting",
    "contributing extra hours would grant you the option to you receive dedicated mentorship from senior staff during the next school term to support your career development",
    "contributing extra hours would grant you more autonomy in school decisions, such as curriculum planning and class management, in the next school term",
    "contributing extra hours would grant you more autonomy in school decisions, such as policy changes and resource planning, in the next school term",
    "contributing extra hours would grant you access to external wellness programs like gym memberships and mental health resources during the next school term",
    "contributing 100 extra hours in a set period of 3 months would fully reimburse a wellness program worth $500 annually",
    "contributing 100 extra hours in a set period of 6 months would fully reimburse a wellness program worth $500 annually",
    "contributing 100 extra hours in a set period of 12 months would fully reimburse a wellness program worth $500 annually",
    "contributing extra hours would cover the cost of a professional certification or further education course of your choice",
    "contributing extra hours would grant you access to physical upgrades for your classroom, such as advanced technology, modern furniture, or improved seating arrangements for students in the next school year",
    "contributing extra hours would grant you access to a dedicated relaxation room equipped with comfortable seating, quiet spaces, and refreshments, during the next school term",
    "contributing extra hours would allow you to choose your preferred teaching methods and class subjects in the next school year",
    "contributing extra hours would provide you access to free or discounted meals in the school cafeteria during the next school term",
    "contributing extra hours would grant you $20 meal vouchers for each five hours worked",
    "contributing extra hours would provide you with opportunities for career advancement and to take on leadership roles in future school projects in the next school year",
    "contributing extra hours would result in a reduced administrative workload during regular work hours in the next school term",
    "contributing extra hours would grant you access to peer support groups and counselling services during the next school term",
    "contributing extra hours would provide you access to on-site childcare facilities during the next school term",
    "contributing extra hours would result in a reduced homework and exam grading load during regular work hours in the next school term",
    "contributing extra hours would provide you with transportation subsidies, such as free public transport passes or fuel discounts, worth $10 for every additional hour you work",
    "contributing extra hours would provide you with access to a reserved or paid car park space on school premises during the next school term",
    "contributing extra hours would provide you with a school-owned car or a novated lease arrangement, which you could drive freely during the next school term",
    "you would be paid your regular hourly rate for these additional hours",
    "you would be paid 1.5 times your regular hourly rate for these additional hours",
    "you would be paid 2 times your regular hourly rate for these additional hours",
    "you would be paid 3 times your regular hourly rate for these additional hours",
    "contributing extra hours would allow you to focus on internal, school-related project such as curriculum design, student well-being programs, or extracurricular development during the next school term",
    "you would have access to an assistant or teaching aide to support you during the next school term",
    "contributing extra hours would allow you to nominate your preferred teaching schedule for the next school term",
    "contributing extra hours would result in reduced class sizes for selected courses or subjects you teach in the next school year",
    "contributing extra hours would grant you priority access to school facilities, such as the library, gym, or auditorium, for personal or professional use during the next school term",
    "contributing extra hours would reward your classroom with a specific budget, allowing you to independently purchase resources, materials, or supplies tailored to your teaching goals during the next school term",
    "you would gain access to personal financial planning or retirement savings advice to help plan for your financial future during the next school term",
    "after contributing a minimum number of 100 additional hours over a set period of 3 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "after contributing a minimum number of 100 additional hours over a set period of 6 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "after contributing a minimum number of 100 extra hours over a set period of 12 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "contributing extra hours would provide you with gift cards or vouchers equivalent to the value of the additional hours you’ve worked for local services, such as restaurants, gyms, or spas",
    "contributing extra hours would provide you with gift cards or vouchers worth $50 for every five hours worked for local services, such as restaurants, gyms, or spas",
    "contributing extra hours would allow you to participate in external, social impact projects that align with your personal interests, such as environmental sustainability initiatives or programs supporting underserved communities, during your regular working hours in the next school term",
    "contributing 100 extra hours over a set period of 3 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing 100 extra hours over a set period of 6 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing 100 extra hours over a set period of 12 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing extra hours would provide you with a one-time financial bonus equivalent to one week of your regular pay",
    "contributing extra hours would result in a personalized gift, such as a high-quality item related to your professional or personal interests (e.g., books, equipment)",
    "contributing extra hours would make you eligible for performance-based incentives, such as a quarterly bonus tied to your department’s success, during the next school year",
    "contributing extra hours would provide a deferred bonus, paid at the end of the school term, equivalent to the number of additional hours worked",
    "contributing extra hours for this specific task would result in a special one-time bonus equivalent to three days’ pay",
    "contributing extra hours would result in an organization-matched contribution to your retirement savings account equivalent to one weeks’ pay",
    "contributing extra hours would reimburse you for a portion of your monthly utility bills (e.g., electricity, internet) for the previous month",
    "contributing extra hours would allow you to choose between several monetary options, such as a cash bonus, gift card, or charitable donation in your name, equivalent to the number of extra hours worked",
    "contributing extra hours would allow you to choose between several monetary options, such as a cash bonus, gift card, or charitable donation in your name, equivalent to half the number of extra hours worked",
    "contributing extra hours would allow you to tailor a personal professional development plan funded by the organization",
    "contributing extra hours would result in public recognition and a tangible memento (e.g., a personalized trophy, framed certificate, or a symbolic token of appreciation)",
    "contributing extra hours would provide early or exclusive access to research findings, teaching materials, or professional insights within your organization",
    "contributing extra hours would result in a donation of equivalent monetary value to a charity or cause of your choice",
    "contributing extra hours would provide tickets to an upcoming cultural or artistic experience, such as a concert, museum tour, or theatre show",
    "contributing extra hours would provide you with discount vouchers for travel or accommodations equivalent to one week's wages",
    "contributing extra hours would provide subsidies for your healthcare expenses, such as dental or vision care, equivalent to the number of extra hours worked",
    "contributing 100 extra hours over a set period of 3 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing 100 extra hours over a set period of 6 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing 100 extra hours over a set period of 12 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing extra hours would enter you into a monthly reward draw for prizes, such as appliances, electronics, or gift cards, equivalent to one weeks’ pay",
    "contributing extra hours would result in monetary milestone bonuses after reaching certain cumulative thresholds (e.g., 20, 50, 100 hours worth 2, 5, and 10 days’ pay, respectively)",
    "contributing extra hours would provide funding or reimbursements for home office improvements, such as furniture or ergonomic equipment, equivalent to one weeks’ pay",
    "contributing extra hours would provide you a reimbursement for up to $300 in teaching supplies or classroom decorations",
    "contributing extra hours would fund a $300 grant for your students' extracurricular activities",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming teaching or education conference worth $300",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming teaching or education conference worth $500",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming teaching or education conference worth $700",
    "contributing extra hours would prompt students to publicly thank you in a school-wide assembly",
    "contributing extra hours would qualify you for a mentorship role with junior teaching staff",
    "contributing extra hours would let you leave early every Friday for the next month",
    "contributing extra hours would secure a $1,000 grant for new books and digital resources for the school library",
    "contributing extra hours would grant a 2% salary increase during the next school term",
    "contributing extra hours would grant a 5% salary increase during the next school term",
    "contributing extra hours would grant a 10% salary increase during the next school term",
    "contributing extra hours would cover the $250 membership fee for a professional teaching organization of your choice",
    "contributing extra hours would grant you a $200 stipend for new professional clothes and footwear",
    "contributing extra hours would allow you to establish a legacy program (e.g., a new club or initiative) that may continue after you leave or retire from the school",
    "contributing extra hours would allow you to exchange administrative tasks for creative projects in the next school term",
    "contributing extra hours would make you eligible for a short-term teacher exchange program (valued at $2,000)",
    "contributing extra hours would allow you to extend maternity or paternity leave by two additional weeks",
    "contributing extra hours would qualify your entire department to receive recognition as the school’s 'Team of the Month'",
    "contributing extra hours would allow you to attend an all-expenses-paid staff retreat (valued at $1,000)",
    "contributing extra hours would contribute directly to a sponsorship fund for underprivileged students, equivalent to the number of extra hours worked",
    "contributing extra hours would provide you access to coaching on balancing demanding work schedules with personal life for the next month",
    "contributing extra hours would provide you access to coaching on balancing demanding work schedules with personal life for the next 3 months",
    "contributing extra hours would qualify your department for a team-building retreat, valued at $3,000",
    "contributing extra hours would provide you with additional paid breaks during your workday in the next school term", # Added Variations from Nursing List
    "contributing extra hours now would allow you to work shorter hours during the next school term",
    "contributing extra hours would provide you with housing allowances or subsidies to help cover your living expenses during the next school term",
    "contributing extra hours would provide full coverage of your professional liability insurance fees in the next school year",
    "contributing extra hours would provide you with mentorship and support to publish articles or research findings in educational journals in the next school year",
    "contributing extra hours would grant you access to on-site massage therapy or counselling services during the next school term",
    "contributing extra hours would give you guaranteed approval for your preferred time-off requests in the next school term",
    "contributing extra hours would provide a one-time contribution to a flexible spending account for medical or dependent care expenses equivalent to one week's pay",
    "contributing extra hours would allow you to spend more one-on-one time with students who need additional support during the next school term, improving their learning experience"
]

#len(teaching_treatment_ids) == len(teaching_treatment_variations)

# Define the categories/types of incentive/reward of the teaching treatments
teaching_treatments_categories = [
    'Work Flexibility',                    # flexible_schedule
    'Time Compensation',                   # time_off_in_lieu
    'Work Flexibility',                    # remote_non_teaching_tasks
    'Career Advancement',                  # fast_track_promotion
    'Career Advancement',                  # current_promotion_opportunity
    'Professional Development',            # training_development_opportunities
    'Public Recognition',                  # public_recognition
    'Professional Development',            # dedicated_mentorship
    'Work Autonomy',                       # autonomy_curriculum_management
    'Work Autonomy',                       # autonomy_policy_planning
    'Wellness Benefits',                   # access_wellness_programs
    'Wellness Benefits',                   # wellness_reimbursement_3months
    'Wellness Benefits',                   # wellness_reimbursement_6months
    'Wellness Benefits',                   # wellness_reimbursement_12months
    'Professional Development',            # cover_education_course
    'Resource Enhancement',                # classroom_physical_upgrades
    'Wellness Benefits',                   # access_relaxation_room
    'Work Autonomy',                       # choose_teaching_methods
    'Wellness Benefits',                   # free_discounted_meals
    'Wellness Benefits',                   # meal_vouchers_20_per_5hours
    'Career Advancement',                  # career_advancement_opportunities
    'Workload Reduction',                  # reduced_admin_workload
    'Wellness Benefits',                   # peer_support_counselling
    'Family Support',                      # access_childcare_facilities
    'Workload Reduction',                  # reduced_grading_load
    'Financial Benefits',                  # transportation_subsidies_10_per_hour
    'Financial Benefits',                  # reserved_parking_space
    'Financial Benefits',                  # access_school_car
    'Direct Compensation',                 # overtime_normal_rate
    'Direct Compensation',                 # overtime_1_5x_rate
    'Direct Compensation',                 # overtime_2x_rate
    'Direct Compensation',                 # overtime_3x_rate
    'Work Focus',                          # focus_internal_projects
    'Support Staff',                       # access_teaching_aide
    'Work Flexibility',                    # choose_teaching_schedule
    'Workload Reduction',                  # reduced_class_sizes
    'Resource Enhancement',                # priority_access_facilities
    'Resource Enhancement',                # classroom_budget_reward
    'Financial Benefits',                  # financial_planning_advice
    'Time Off',                            # paid_sabbatical_3months
    'Time Off',                            # paid_sabbatical_6months
    'Time Off',                            # paid_sabbatical_12months
    'Financial Benefits',                  # gift_cards_equal_hours
    'Financial Benefits',                  # gift_cards_50_per_5hours
    'Community Engagement',                # participate_social_projects
    'Wellness Benefits',                   # holiday_package_3months
    'Wellness Benefits',                   # holiday_package_6months
    'Wellness Benefits',                   # holiday_package_12months
    'Financial Benefits',                  # one_time_bonus_1week_pay
    'Recognition',                         # personalized_gift
    'Performance Incentives',              # performance_based_incentives
    'Financial Benefits',                  # deferred_bonus_equal_hours
    'Financial Benefits',                  # special_bonus_3days_pay
    'Retirement Benefits',                 # retirement_contribution_1week_pay
    'Financial Benefits',                  # utility_bills_reimbursement
    'Financial Benefits',                  # monetary_options_equal_hours
    'Financial Benefits',                  # monetary_options_half_hours
    'Professional Development',            # personal_development_plan
    'Recognition',                         # recognition_with_memento
    'Professional Development',            # exclusive_access_resources
    'Community Engagement',                # charity_donation_equal_value
    'Wellness Benefits',                   # tickets_cultural_event
    'Wellness Benefits',                   # travel_vouchers_1week_wage
    'Wellness Benefits',                   # healthcare_subsidies_equal_hours
    'Financial Benefits',                  # tech_upgrade_subsidy_3months
    'Financial Benefits',                  # tech_upgrade_subsidy_6months
    'Financial Benefits',                  # tech_upgrade_subsidy_12months
    'Performance Incentives',              # monthly_reward_draw
    'Performance Incentives',              # milestone_bonuses
    'Financial Benefits',                  # home_office_improvements
    'Financial Benefits',                  # reimbursement_teaching_supplies_300
    'Financial Benefits',                  # grant_students_extracurricular_300
    'Professional Development',            # conference_attendance_300
    'Professional Development',            # conference_attendance_500
    'Professional Development',            # conference_attendance_700
    'Recognition',                         # student_public_thanks
    'Professional Development',            # mentorship_role_junior_staff
    'Work Flexibility',                    # leave_early_fridays_1month
    'Resource Enhancement',                # grant_school_library_1000
    'Direct Compensation',                 # salary_increase_2_percent
    'Direct Compensation',                 # salary_increase_5_percent
    'Direct Compensation',                 # salary_increase_10_percent
    'Professional Development',            # membership_fee_covered_250
    'Financial Benefits',                  # stipend_professional_attire_200
    'Legacy Building',                     # establish_legacy_program
    'Work Flexibility',                    # exchange_admin_for_creative
    'Professional Development',            # teacher_exchange_program_2000
    'Family Support',                      # extend_parental_leave_2weeks
    'Recognition',                         # department_team_of_month
    'Wellness Benefits',                   # staff_retreat_1000
    'Community Engagement',                # sponsorship_fund_students
    'Wellness Benefits',                   # work_life_coaching_1month
    'Wellness Benefits',                   # work_life_coaching_3months
    'Wellness Benefits',                   # department_team_building_3000
    'Wellness Benefits',                   # additional_paid_breaks
    'Work Flexibility',                    # work_shorter_hours
    'Financial Benefits',                  # housing_allowance
    'Financial Benefits',                  # insurance_coverage
    'Professional Development',            # mentorship_for_publication
    'Wellness Benefits',                   # access_massage_counselling
    'Work Flexibility',                    # guaranteed_time_off_requests
    'Financial Benefits',                  # flexible_spending_account
    'Workload Reduction'                   # extra_time_with_students
]

# Define the intrinsic (1) to extrinsic (7) scale of the teaching treatments
teaching_treatments_numeric_values = [
    1,  # flexible_schedule
    3,  # time_off_in_lieu
    1,  # remote_non_teaching_tasks
    4,  # fast_track_promotion
    4,  # current_promotion_opportunity
    4,  # training_development_opportunities
    0,  # public_recognition
    3,  # dedicated_mentorship
    2,  # autonomy_curriculum_management
    2,  # autonomy_policy_planning
    2,  # access_wellness_programs
    5,  # wellness_reimbursement_3months
    5,  # wellness_reimbursement_6months
    5,  # wellness_reimbursement_12months
    4,  # cover_education_course
    3,  # classroom_physical_upgrades
    2,  # access_relaxation_room
    2,  # choose_teaching_methods
    3,  # free_discounted_meals
    5,  # meal_vouchers_20_per_5hours
    4,  # career_advancement_opportunities
    2,  # reduced_admin_workload
    2,  # peer_support_counselling
    3,  # access_childcare_facilities
    2,  # reduced_grading_load
    5,  # transportation_subsidies_10_per_hour
    5,  # reserved_parking_space
    6,  # access_school_car
    6,  # overtime_normal_rate
    6,  # overtime_1_5x_rate
    6,  # overtime_2x_rate
    7,  # overtime_3x_rate
    2,  # focus_internal_projects
    3,  # access_teaching_aide
    1,  # choose_teaching_schedule
    2,  # reduced_class_sizes
    2,  # priority_access_facilities
    4,  # classroom_budget_reward
    2,  # financial_planning_advice
    5,  # paid_sabbatical_3months
    6,  # paid_sabbatical_6months
    7,  # paid_sabbatical_12months
    5,  # gift_cards_equal_hours
    5,  # gift_cards_50_per_5hours
    2,  # participate_social_projects
    5,  # holiday_package_3months
    6,  # holiday_package_6months
    7,  # holiday_package_12months
    5,  # one_time_bonus_1week_pay
    3,  # personalized_gift
    5,  # performance_based_incentives
    5,  # deferred_bonus_equal_hours
    5,  # special_bonus_3days_pay
    5,  # retirement_contribution_1week_pay
    5,  # utility_bills_reimbursement
    5,  # monetary_options_equal_hours
    5,  # monetary_options_half_hours
    3,  # personal_development_plan
    1,  # recognition_with_memento
    2,  # exclusive_access_resources
    5,  # charity_donation_equal_value
    4,  # tickets_cultural_event
    5,  # travel_vouchers_1week_wage
    5,  # healthcare_subsidies_equal_hours
    5,  # tech_upgrade_subsidy_3months
    6,  # tech_upgrade_subsidy_6months
    7,  # tech_upgrade_subsidy_12months
    5,  # monthly_reward_draw
    5,  # milestone_bonuses
    5,  # home_office_improvements
    5,  # reimbursement_teaching_supplies_300
    5,  # grant_students_extracurricular_300
    5,  # conference_attendance_300
    5,  # conference_attendance_500
    6,  # conference_attendance_700
    0,  # student_public_thanks
    3,  # mentorship_role_junior_staff
    1,  # leave_early_fridays_1month
    5,  # grant_school_library_1000
    5,  # salary_increase_2_percent
    6,  # salary_increase_5_percent
    7,  # salary_increase_10_percent
    5,  # membership_fee_covered_250
    5,  # stipend_professional_attire_200
    3,  # establish_legacy_program
    1,  # exchange_admin_for_creative
    6,  # teacher_exchange_program_2000
    5,  # extend_parental_leave_2weeks
    0,  # department_team_of_month
    5,  # staff_retreat_1000
    5,  # sponsorship_fund_students
    2,  # work_life_coaching_1month
    3,  # work_life_coaching_3months
    6,  # department_team_building_3000
    2,  # additional_paid_breaks
    1,  # work_shorter_hours
    5,  # housing_allowance
    5,  # insurance_coverage
    3,  # mentorship_for_publication
    2,  # access_massage_counselling
    1,  # guaranteed_time_off_requests
    5,  # flexible_spending_account
    2   # extra_time_with_students
]

# Define the monetary value of the teaching treatments
# Note: The monetary values are specified where applicable. For rewards without direct monetary equivalents or intrinsic rewards, the value is set to 0 or described qualitatively.
teaching_treatments_monetary_values = [
    0,                                  # flexible_schedule
    'Equivalent to extra hours worked', # time_off_in_lieu
    0,                                  # remote_non_teaching_tasks
    0,                                  # fast_track_promotion
    0,                                  # current_promotion_opportunity
    0,                                  # training_development_opportunities
    0,                                  # public_recognition
    0,                                  # dedicated_mentorship
    0,                                  # autonomy_curriculum_management
    0,                                  # autonomy_policy_planning
    0,                                  # access_wellness_programs
    '$500',                             # wellness_reimbursement_3months
    '$500',                             # wellness_reimbursement_6months
    '$500',                             # wellness_reimbursement_12months
    'Cost of course',                   # cover_education_course
    0,                                  # classroom_physical_upgrades
    0,                                  # access_relaxation_room
    0,                                  # choose_teaching_methods
    0,                                  # free_discounted_meals
    '$20 per 5 hours',                  # meal_vouchers_20_per_5hours
    0,                                  # career_advancement_opportunities
    0,                                  # reduced_admin_workload
    0,                                  # peer_support_counselling
    0,                                  # access_childcare_facilities
    0,                                  # reduced_grading_load
    '$10 per hour',                     # transportation_subsidies_10_per_hour
    0,                                  # reserved_parking_space
    0,                                  # access_school_car
    'Regular hourly rate',              # overtime_normal_rate
    '1.5x hourly rate',                 # overtime_1_5x_rate
    '2x hourly rate',                   # overtime_2x_rate
    '3x hourly rate',                   # overtime_3x_rate
    0,                                  # focus_internal_projects
    0,                                  # access_teaching_aide
    0,                                  # choose_teaching_schedule
    0,                                  # reduced_class_sizes
    0,                                  # priority_access_facilities
    0,                                  # classroom_budget_reward
    0,                                  # financial_planning_advice
    'Equivalent to salary during sabbatical', # paid_sabbatical_3months
    'Equivalent to salary during sabbatical', # paid_sabbatical_6months
    'Equivalent to salary during sabbatical', # paid_sabbatical_12months
    'Equivalent to extra hours worked', # gift_cards_equal_hours
    '$50 per 5 hours',                  # gift_cards_50_per_5hours
    0,                                  # participate_social_projects
    'Two weeks’ wages',                 # holiday_package_3months
    'Two weeks’ wages',                 # holiday_package_6months
    'Two weeks’ wages',                 # holiday_package_12months
    'One week’s pay',                   # one_time_bonus_1week_pay
    0,                                  # personalized_gift
    0,                                  # performance_based_incentives
    'Equivalent to extra hours worked', # deferred_bonus_equal_hours
    'Three days’ pay',                  # special_bonus_3days_pay
    'One week’s pay',                   # retirement_contribution_1week_pay
    'Portion of utility bills',         # utility_bills_reimbursement
    'Equivalent to extra hours worked', # monetary_options_equal_hours
    'Half the extra hours worked',      # monetary_options_half_hours
    0,                                  # personal_development_plan
    0,                                  # recognition_with_memento
    0,                                  # exclusive_access_resources
    'Equivalent monetary value',        # charity_donation_equal_value
    0,                                  # tickets_cultural_event
    'One week’s wages',                 # travel_vouchers_1week_wage
    'Equivalent to extra hours worked', # healthcare_subsidies_equal_hours
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_3months
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_6months
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_12months
    'One week’s pay',                   # monthly_reward_draw
    'Monetary bonuses at milestones',   # milestone_bonuses
    'One week’s pay',                   # home_office_improvements
    '$300',                             # reimbursement_teaching_supplies_300
    '$300',                             # grant_students_extracurricular_300
    '$300',                             # conference_attendance_300
    '$500',                             # conference_attendance_500
    '$700',                             # conference_attendance_700
    0,                                  # student_public_thanks
    0,                                  # mentorship_role_junior_staff
    0,                                  # leave_early_fridays_1month
    '$1,000',                           # grant_school_library_1000
    '2% salary increase',               # salary_increase_2_percent
    '5% salary increase',               # salary_increase_5_percent
    '10% salary increase',              # salary_increase_10_percent
    '$250',                             # membership_fee_covered_250
    '$200',                             # stipend_professional_attire_200
    0,                                  # establish_legacy_program
    0,                                  # exchange_admin_for_creative
    '$2,000',                           # teacher_exchange_program_2000
    0,                                  # extend_parental_leave_2weeks
    0,                                  # department_team_of_month
    '$1,000',                           # staff_retreat_1000
    'Equivalent to extra hours worked', # sponsorship_fund_students
    0,                                  # work_life_coaching_1month
    0,                                  # work_life_coaching_3months
    '$3,000',                           # department_team_building_3000
    0,                                  # additional_paid_breaks
    0,                                  # work_shorter_hours
    0,                                  # housing_allowance
    0,                                  # insurance_coverage
    0,                                  # mentorship_for_publication
    0,                                  # access_massage_counselling
    0,                                  # guaranteed_time_off_requests
    'One week’s pay',                   # flexible_spending_account
    0                                   # extra_time_with_students
]

#len(teaching_treatment_ids) == len(teaching_treatment_variations) == len(teaching_treatments_categories) == len(teaching_treatments_numeric_values) == len(teaching_treatments_monetary_values)

# Generate dictionary of lists, pandas dataframe and write to excel file
teacher_dict = {'id': teaching_treatment_ids, 'treatment': teaching_treatment_variations, 'category': teaching_treatments_categories, 'intrinsic_extrinsic_scale': teaching_treatments_numeric_values, 'monetary_value': teaching_treatments_monetary_values}
teacher_df = pd.DataFrame(teacher_dict)
teacher_df.to_excel('./data/inputs/treatment_combinations/teacher_treatments_metadata.xlsx', index=False)

# Nursing scenarios
nursing_scenarios = [
    "You are a nurse working in a hospital, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff to assist with specialized care (e.g., ICU, neonatal units). How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff in the Emergency Department. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff to help with patient documentation and other administrative tasks. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff to conduct patient education sessions (e.g., managing chronic illnesses, post-discharge care). How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff to assist in surgical procedures. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff due to recent government funding cuts or policy changes that have limited resources available for your department. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff because many of your colleagues have recently resigned or left their positions. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff because key infrastructure, such as equipment or facilities, has been temporarily damaged or is under repair. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff due to a recent natural disaster or shock event, such as a flood or wildfire, which has placed significant strain on the healthcare system. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff due to a supply chain error that delayed the delivery of essential medical equipment, creating a backlog of patient care needs. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff for a community health initiative, such as conducting free vaccinations for underserved populations. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff due to a sudden flu outbreak affecting many of your colleagues. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff caused by organizational mismanagement, such as over-scheduling leave for multiple staff members at the same time. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff to provide specialized paediatric care for children in need. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?"
]

# Define short prefixes/descriptors for the teacher scenarios
nursing_scenarios_prefixes = [
    "nurse_baseline_treatment",
    "nurse_specialised_care",
    "nurse_emergency_department",
    "nurse_admin_backlog",
    "nurse_patient_education",
    "nurse_surgical_assistance",
    "nurse_government_changes",
    "nurse_recent_resignations",
    "nurse_infrastructure_repairs",
    "nurse_natural_disaster",
    "nurse_external_contractor",
    "nurse_community_project",
    "nurse_flu_outbreak",
    "nurse_organisational_mismanagement",
    "nurse_children_in_need"
]

#len(nursing_scenarios) == len(nursing_scenarios_prefixes)

# Nursing treatment IDs
nursing_treatment_ids = [
    'flexible_schedule',
    'time_off_in_lieu',
    'remote_non_clinical_tasks',
    'cover_education_course',
    'dedicated_mentorship',
    'public_recognition',
    'fast_track_promotion',
    'access_wellness_programs',
    'wellness_reimbursement_3months',
    'wellness_reimbursement_6months',
    'wellness_reimbursement_12months',
    'access_relaxation_room',
    'free_discounted_meals',
    'meal_vouchers_20_per_5hours',
    'transportation_subsidies_10_per_hour',
    'reserved_parking_space',
    'access_hospital_car',
    'overtime_normal_rate',
    'overtime_1_5x_rate',
    'overtime_2x_rate',
    'overtime_3x_rate',
    'department_equipment_upgrades',
    'access_assistant_aide',
    'reduced_patient_loads',
    'priority_access_facilities',
    'paid_sabbatical_3months',
    'paid_sabbatical_6months',
    'paid_sabbatical_12months',
    'participate_community_initiatives',
    'additional_paid_breaks',
    'work_shorter_shifts',
    'flexible_shift_times',
    'one_time_bonus_1week_pay',
    'special_bonus_3days_pay',
    'housing_allowance',
    'utility_bills_reimbursement',
    'insurance_coverage',
    'uniform_equipment_allowance',
    'conference_attendance_300',
    'conference_attendance_500',
    'conference_attendance_700',
    'mentorship_for_publication',
    'access_massage_counselling',
    'lead_improvement_projects',
    'increased_policy_influence',
    'guaranteed_time_off_requests',
    'exclusively_day_shifts',
    'flexible_spending_account',
    'retirement_contribution_1week_pay',
    'monetary_options_equal_hours',
    'monetary_options_half_hours',
    'personal_development_plan',
    'recognition_with_memento',
    'exclusive_access_resources',
    'charity_donation_equal_value',
    'tickets_cultural_event',
    'travel_vouchers_1week_wage',
    'gift_cards_equal_hours',
    'gift_cards_50_per_5hours',
    'healthcare_subsidies_equal_hours',
    'tech_upgrade_subsidy_3months',
    'tech_upgrade_subsidy_6months',
    'tech_upgrade_subsidy_12months',
    'monthly_reward_draw',
    'milestone_bonuses',
    'home_office_improvements',
    'grant_department_extracurricular_300',
    'patient_public_thanks',
    'mentorship_role_junior_staff',
    'leave_early_fridays_1month',
    'grant_hospital_library_1000',
    'salary_increase_2_percent',
    'salary_increase_5_percent',
    'salary_increase_10_percent',
    'membership_fee_covered_250',
    'stipend_uniforms_footwear_200',
    'establish_legacy_program',
    'extra_time_with_patients',
    'nursing_exchange_program_2000',
    'extend_parental_leave_2weeks',
    'team_of_month_recognition',
    'staff_retreat_1000',
    'sponsorship_fund_patients',
    'work_life_coaching_1month',
    'work_life_coaching_3months',
    'unit_team_building_3000',
    'reduced_admin_workload', # Added from Teaching List
    'peer_support_counselling',
    'access_childcare_facilities',
    'financial_planning_advice',
    'holiday_package_3months',
    'holiday_package_6months',
    'holiday_package_12months',
    'personalized_gift',
    'performance_based_incentives',
    'deferred_bonus_equal_hours',
    'exchange_admin_for_creative'
]

# Nursing treatment variations
nursing_treatment_variations = [
    "contributing extra hours would grant you the option to flexibly set your own schedule during regular work hours in the next rotation",
    "you would be compensated with time off in lieu equivalent to the number of additional hours you’ve worked",
    "contributing extra hours would grant you the option to perform certain non-clinical tasks (e.g., documentation or telehealth consultations) remotely during the next rotation",
    "contributing extra hours would cover the cost of a professional certification or further education course of your choice",
    "contributing extra hours would grant you the option to you receive dedicated mentorship from senior staff during the next rotation, to support your career development",
    "your efforts would be publicly recognized in the next hospital newsletter and whole-of-hospital staff meeting",
    "contributing extra hours would grant you early consideration for promotions or fast-tracking in the promotion review process in the next calendar year",
    "contributing extra hours would grant you access to external wellness programs like gym memberships, mental health counselling, or yoga classes, during the next rotation",
    "contributing 100 extra hours in a set period of 3 months would fully reimburse a wellness program worth $500 annually",
    "contributing 100 extra hours in a set period of 6 months would fully reimburse a wellness program worth $500 annually",
    "contributing 100 extra hours in a set period of 12 months would fully reimburse a wellness program worth $500 annually",
    "contributing extra hours would grant you access to a dedicated relaxation room equipped with comfortable seating, quiet spaces, and refreshments, during the next rotation",
    "contributing extra hours would provide you access to free or discounted meals in the hospital cafeteria during the next rotation",
    "contributing extra hours would grant you $20 meal vouchers for each five hours worked",
    "contributing extra hours would provide you with transportation subsidies, such as free public transport passes or fuel discounts, worth $10 for every additional hour you work",
    "contributing extra hours would provide you with access to a reserved or paid car park space on hospital premises during the next rotation",
    "contributing extra hours would provide you with a hospital-owned car or a novated lease arrangement, which you could drive freely during the next rotation",
    "you would be paid your regular hourly rate for these additional hours",
    "you would be paid 1.5 times your regular hourly rate for these additional hours",
    "you would be paid 2 times your regular hourly rate for these additional hours",
    "you would be paid 3 times your regular hourly rate for these additional hours",
    "contributing extra hours would provide your department with access to advanced medical equipment or upgrades to existing tools in the next calendar year",
    "contributing extra hours would provide you access to an assistant or aide to support you during your shifts in the next rotation",
    "contributing extra hours would result in reduced patient loads for selected shifts in the next rotation",
    "contributing extra hours would grant you priority access to hospital facilities, such as private study rooms or the staff gym, during the next rotation",
    "after contributing a minimum number of 100 additional hours over a set period of 3 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "after contributing a minimum number of 100 additional hours over a set period of 6 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "after contributing a minimum number of 100 additional hours over a set period of 12 months, you could qualify for a paid sabbatical to pursue professional development or personal projects",
    "contributing extra hours would allow you to lead or participate in community-focused healthcare initiatives, such as vaccination drives or health awareness campaigns/education workshops, during your normal working hours in the next rotation",
    "contributing extra hours would provide you with additional paid breaks during your shifts in the next rotation",
    "contributing extra hours now would allow you to work shorter shifts during the next rotation",
    "contributing extra hours would give you flexibility to start or end your shifts earlier/later than usual in the next rotation",
    "contributing extra hours would provide you with a one-time financial bonus equivalent to one week of your regular pay",
    "contributing extra hours for this specific task would result in a special one-time bonus equivalent to three days’ pay",
    "contributing extra hours would provide you with housing allowances or subsidies to help cover your living expenses during the next rotation",
    "contributing extra hours would reimburse you for a portion of your monthly utility bills (e.g., electricity, internet) for the previous month",
    "contributing extra hours would provide full coverage of your professional liability insurance fees in the next calendar year",
    "contributing extra hours would provide you with an additional allowance for uniforms and personal equipment during the next rotation",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming nursing or healthcare conference worth $300",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming nursing or healthcare conference worth $500",
    "contributing extra hours would make you eligible for a fully-sponsored attendance at an upcoming nursing or healthcare conference worth $700",
    "contributing extra hours would provide you with mentorship and support to publish articles or research findings in nursing journals in the next calendar year",
    "contributing extra hours would grant you access to on-site massage therapy or counselling services during the next rotation",
    "contributing extra hours would allow you to lead or coordinate hospital-wide improvement projects in the next calendar year",
    "contributing extra hours would provide you with increased influence over policies within your department or unit during the next rotation",
    "contributing extra hours would give you guaranteed approval for your preferred time-off requests in the next rotation",
    "contributing extra hours would result in exclusively day shifts for the next rotation",
    "contributing extra hours would provide a one-time contribution to a flexible spending account for medical or dependent care expenses equivalent to one weeks’ pay",
    "contributing extra hours would result in an organization-matched contribution to your retirement savings account equivalent to one weeks’ pay",
    "contributing extra hours would allow you to choose between several monetary options, such as a cash bonus, gift card, or charitable donation in your name, equivalent to the number of extra hours worked",
    "contributing extra hours would allow you to choose between several monetary options, such as a cash bonus, gift card, or charitable donation in your name, equivalent to half the number of extra hours worked",
    "contributing extra hours would allow you to tailor a personal professional development plan funded by the organization",
    "contributing extra hours would result in public recognition and a tangible memento (e.g., a personalized trophy, framed certificate, or a symbolic token of appreciation)",
    "contributing extra hours would provide early or exclusive access to research findings, learning materials, or professional insights within your organization",
    "contributing extra hours would result in a donation of equivalent monetary value to a charity or cause of your choice",
    "contributing extra hours would provide tickets to an upcoming cultural or artistic experience, such as a concert, museum tour, or theatre show",
    "contributing extra hours would provide you with discount vouchers for travel or accommodations equivalent to one week's wages",
    "contributing extra hours would provide you with gift cards or vouchers equivalent to the value of the additional hours you’ve worked for local services, such as restaurants, gyms, or spas",
    "contributing extra hours would provide you with gift cards or vouchers worth $50 for every five hours worked for local services, such as restaurants, gyms, or spas",
    "contributing extra hours would provide subsidies for your healthcare expenses, such as dental or vision care, equivalent to the number of extra hours worked",
    "contributing 100 extra hours over a set period of 3 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing 100 extra hours over a set period of 6 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing 100 extra hours over a set period of 12 months would provide a subsidy or reimbursement for a personal technology upgrade, such as a phone, laptop or tablet",
    "contributing extra hours would enter you into a monthly reward draw for prizes, such as appliances, electronics, or gift cards, equivalent to one weeks’ pay",
    "contributing extra hours would result in monetary milestone bonuses after reaching certain cumulative thresholds (e.g., 20, 50, 100 hours worth 2, 5, and 10 days’ pay, respectively)",
    "contributing extra hours would provide funding or reimbursements for home office improvements, such as furniture or ergonomic equipment, equivalent to one weeks’ pay",
    "contributing extra hours would fund a $300 grant for your departments’ extracurricular activities",
    "contributing extra hours would prompt patients to publicly thank you in front of your supervisor",
    "contributing extra hours would qualify you for a mentorship role with junior nursing staff",
    "contributing extra hours would let you leave early every Friday that you are rostered on for the next month",
    "contributing extra hours would secure a $1,000 grant for new books and digital resources for the hospital library",
    "contributing extra hours would grant a 2% salary increase during the next rotation",
    "contributing extra hours would grant a 5% salary increase during the next rotation",
    "contributing extra hours would grant a 10% salary increase during the next rotation",
    "contributing extra hours would cover the $250 membership fee for a professional nursing organization of your choice",
    "contributing extra hours would grant you a $200 stipend for new uniforms and footwear",
    "contributing extra hours would allow you to establish a legacy program (e.g., a new club or initiative) that may continue after you leave or retire from the hospital",
    "contributing extra hours would allow you to spend more one-on-one time with your favourite long-term care patients during the next rotation, improving their recovery experience",
    "contributing extra hours would make you eligible for a short-term nursing exchange program (valued at $2,000)",
    "contributing extra hours would allow you to extend maternity or paternity leave by two additional weeks",
    "contributing extra hours would qualify your entire team to receive recognition as the hospital’s 'Team of the Month'",
    "contributing extra hours would allow you to attend an all-expenses-paid staff retreat (valued at $1,000)",
    "contributing extra hours would contribute directly to a sponsorship fund for underprivileged patients, equivalent to the number of extra hours worked",
    "contributing extra hours would provide you access to coaching on balancing demanding work schedules with personal life for the next month",
    "contributing extra hours would provide you access to coaching on balancing demanding work schedules with personal life for the next 3 months",
    "contributing extra hours would qualify your unit for a team-building retreat, valued at $3,000",
    "contributing extra hours would result in a reduced administrative workload during regular work hours in the next rotation", # Added Variations from Teaching List
    "contributing extra hours would grant you access to peer support groups and counselling services during the next rotation",
    "contributing extra hours would provide you access to on-site childcare facilities during the next rotation",
    "you would gain access to personal financial planning or retirement savings advice to help plan for your financial future during the next rotation",
    "contributing 100 extra hours over a set period of 3 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing 100 extra hours over a set period of 6 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing 100 extra hours over a set period of 12 months would provide you with a holiday package valued at two weeks of your regular wages",
    "contributing extra hours would result in a personalized gift, such as a high-quality item related to your professional or personal interests (e.g., books, equipment)",
    "contributing extra hours would make you eligible for performance-based incentives, such as a quarterly bonus tied to your department's success, during the next calendar year",
    "contributing extra hours would provide a deferred bonus, paid at the end of the rotation, equivalent to the number of additional hours worked",
    "contributing extra hours would allow you to exchange administrative tasks for more engaging clinical responsibilities in the next rotation"
]

#len(nursing_treatment_ids) == len(nursing_treatment_variations)

# Define the categories/types of incentive/reward of the nursing treatments
nursing_treatments_categories = [
    'Work Flexibility',                    # flexible_schedule
    'Time Compensation',                   # time_off_in_lieu
    'Work Flexibility',                    # remote_non_clinical_tasks
    'Professional Development',            # cover_education_course
    'Professional Development',            # dedicated_mentorship
    'Public Recognition',                  # public_recognition
    'Career Advancement',                  # fast_track_promotion
    'Wellness Benefits',                   # access_wellness_programs
    'Wellness Benefits',                   # wellness_reimbursement_3months
    'Wellness Benefits',                   # wellness_reimbursement_6months
    'Wellness Benefits',                   # wellness_reimbursement_12months
    'Wellness Benefits',                   # access_relaxation_room
    'Wellness Benefits',                   # free_discounted_meals
    'Wellness Benefits',                   # meal_vouchers_20_per_5hours
    'Financial Benefits',                  # transportation_subsidies_10_per_hour
    'Financial Benefits',                  # reserved_parking_space
    'Financial Benefits',                  # access_hospital_car
    'Direct Compensation',                 # overtime_normal_rate
    'Direct Compensation',                 # overtime_1_5x_rate
    'Direct Compensation',                 # overtime_2x_rate
    'Direct Compensation',                 # overtime_3x_rate
    'Resource Enhancement',                # department_equipment_upgrades
    'Support Staff',                       # access_assistant_aide
    'Workload Reduction',                  # reduced_patient_loads
    'Resource Enhancement',                # priority_access_facilities
    'Time Off',                            # paid_sabbatical_3months
    'Time Off',                            # paid_sabbatical_6months
    'Time Off',                            # paid_sabbatical_12months
    'Community Engagement',                # participate_community_initiatives
    'Wellness Benefits',                   # additional_paid_breaks
    'Work Flexibility',                    # work_shorter_shifts
    'Work Flexibility',                    # flexible_shift_times
    'Financial Benefits',                  # one_time_bonus_1week_pay
    'Financial Benefits',                  # special_bonus_3days_pay
    'Financial Benefits',                  # housing_allowance
    'Financial Benefits',                  # utility_bills_reimbursement
    'Financial Benefits',                  # insurance_coverage
    'Financial Benefits',                  # uniform_equipment_allowance
    'Professional Development',            # conference_attendance_300
    'Professional Development',            # conference_attendance_500
    'Professional Development',            # conference_attendance_700
    'Professional Development',            # mentorship_for_publication
    'Wellness Benefits',                   # access_massage_counselling
    'Professional Development',            # lead_improvement_projects
    'Work Autonomy',                       # increased_policy_influence
    'Work Flexibility',                    # guaranteed_time_off_requests
    'Work Flexibility',                    # exclusively_day_shifts
    'Financial Benefits',                  # flexible_spending_account
    'Retirement Benefits',                 # retirement_contribution_1week_pay
    'Financial Benefits',                  # monetary_options_equal_hours
    'Financial Benefits',                  # monetary_options_half_hours
    'Professional Development',            # personal_development_plan
    'Recognition',                         # recognition_with_memento
    'Professional Development',            # exclusive_access_resources
    'Community Engagement',                # charity_donation_equal_value
    'Wellness Benefits',                   # tickets_cultural_event
    'Wellness Benefits',                   # travel_vouchers_1week_wage
    'Financial Benefits',                  # gift_cards_equal_hours
    'Financial Benefits',                  # gift_cards_50_per_5hours
    'Wellness Benefits',                   # healthcare_subsidies_equal_hours
    'Financial Benefits',                  # tech_upgrade_subsidy_3months
    'Financial Benefits',                  # tech_upgrade_subsidy_6months
    'Financial Benefits',                  # tech_upgrade_subsidy_12months
    'Performance Incentives',              # monthly_reward_draw
    'Performance Incentives',              # milestone_bonuses
    'Financial Benefits',                  # home_office_improvements
    'Financial Benefits',                  # grant_department_extracurricular_300
    'Recognition',                         # patient_public_thanks
    'Professional Development',            # mentorship_role_junior_staff
    'Work Flexibility',                    # leave_early_fridays_1month
    'Resource Enhancement',                # grant_hospital_library_1000
    'Direct Compensation',                 # salary_increase_2_percent
    'Direct Compensation',                 # salary_increase_5_percent
    'Direct Compensation',                 # salary_increase_10_percent
    'Professional Development',            # membership_fee_covered_250
    'Financial Benefits',                  # stipend_uniforms_footwear_200
    'Legacy Building',                     # establish_legacy_program
    'Workload Reduction',                  # extra_time_with_patients
    'Professional Development',            # nursing_exchange_program_2000
    'Family Support',                      # extend_parental_leave_2weeks
    'Recognition',                         # team_of_month_recognition
    'Wellness Benefits',                   # staff_retreat_1000
    'Community Engagement',                # sponsorship_fund_patients
    'Wellness Benefits',                   # work_life_coaching_1month
    'Wellness Benefits',                   # work_life_coaching_3months
    'Wellness Benefits',                   # unit_team_building_3000
    'Workload Reduction',                  # reduced_admin_workload
    'Wellness Benefits',                   # peer_support_counselling
    'Family Support',                      # access_childcare_facilities
    'Financial Benefits',                  # financial_planning_advice
    'Wellness Benefits',                   # holiday_package_3months
    'Wellness Benefits',                   # holiday_package_6months
    'Wellness Benefits',                   # holiday_package_12months
    'Recognition',                         # personalized_gift
    'Performance Incentives',              # performance_based_incentives
    'Financial Benefits',                  # deferred_bonus_equal_hours
    'Work Flexibility'                     # exchange_admin_for_creative
]

# Define the intrinsic (1) to extrinsic (7) scale of the nursing treatments
nursing_treatments_numeric_values = [
    1,  # flexible_schedule
    3,  # time_off_in_lieu
    1,  # remote_non_clinical_tasks
    4,  # cover_education_course
    3,  # dedicated_mentorship
    0,  # public_recognition
    4,  # fast_track_promotion
    2,  # access_wellness_programs
    5,  # wellness_reimbursement_3months
    5,  # wellness_reimbursement_6months
    5,  # wellness_reimbursement_12months
    2,  # access_relaxation_room
    3,  # free_discounted_meals
    5,  # meal_vouchers_20_per_5hours
    5,  # transportation_subsidies_10_per_hour
    5,  # reserved_parking_space
    6,  # access_hospital_car
    6,  # overtime_normal_rate
    6,  # overtime_1_5x_rate
    6,  # overtime_2x_rate
    7,  # overtime_3x_rate
    3,  # department_equipment_upgrades
    3,  # access_assistant_aide
    2,  # reduced_patient_loads
    2,  # priority_access_facilities
    5,  # paid_sabbatical_3months
    6,  # paid_sabbatical_6months
    7,  # paid_sabbatical_12months
    2,  # participate_community_initiatives
    2,  # additional_paid_breaks
    1,  # work_shorter_shifts
    1,  # flexible_shift_times
    5,  # one_time_bonus_1week_pay
    5,  # special_bonus_3days_pay
    5,  # housing_allowance
    5,  # utility_bills_reimbursement
    5,  # insurance_coverage
    5,  # uniform_equipment_allowance
    5,  # conference_attendance_300
    5,  # conference_attendance_500
    6,  # conference_attendance_700
    3,  # mentorship_for_publication
    2,  # access_massage_counselling
    3,  # lead_improvement_projects
    2,  # increased_policy_influence
    1,  # guaranteed_time_off_requests
    2,  # exclusively_day_shifts
    5,  # flexible_spending_account
    5,  # retirement_contribution_1week_pay
    5,  # monetary_options_equal_hours
    5,  # monetary_options_half_hours
    3,  # personal_development_plan
    1,  # recognition_with_memento
    2,  # exclusive_access_resources
    5,  # charity_donation_equal_value
    4,  # tickets_cultural_event
    5,  # travel_vouchers_1week_wage
    5,  # gift_cards_equal_hours
    5,  # gift_cards_50_per_5hours
    5,  # healthcare_subsidies_equal_hours
    5,  # tech_upgrade_subsidy_3months
    6,  # tech_upgrade_subsidy_6months
    7,  # tech_upgrade_subsidy_12months
    5,  # monthly_reward_draw
    5,  # milestone_bonuses
    5,  # home_office_improvements
    5,  # grant_department_extracurricular_300
    0,  # patient_public_thanks
    3,  # mentorship_role_junior_staff
    1,  # leave_early_fridays_1month
    5,  # grant_hospital_library_1000
    5,  # salary_increase_2_percent
    6,  # salary_increase_5_percent
    7,  # salary_increase_10_percent
    5,  # membership_fee_covered_250
    5,  # stipend_uniforms_footwear_200
    3,  # establish_legacy_program
    2,  # extra_time_with_patients
    6,  # nursing_exchange_program_2000
    5,  # extend_parental_leave_2weeks
    0,  # team_of_month_recognition
    5,  # staff_retreat_1000
    5,  # sponsorship_fund_patients
    2,  # work_life_coaching_1month
    3,  # work_life_coaching_3months
    6,  # unit_team_building_3000
    2,  # reduced_admin_workload
    2,  # peer_support_counselling
    3,  # access_childcare_facilities
    2,  # financial_planning_advice
    5,  # holiday_package_3months
    6,  # holiday_package_6months
    7,  # holiday_package_12months
    3,  # personalized_gift
    5,  # performance_based_incentives
    5,  # deferred_bonus_equal_hours
    1   # exchange_admin_for_creative
]

# Define the monetary value of the nursing treatments
# Note: The monetary values are specified where applicable. For rewards without direct monetary equivalents or intrinsic rewards, the value is set to 0 or described qualitatively.
nursing_treatments_monetary_values = [
    0,                                  # flexible_schedule
    'Equivalent to extra hours worked', # time_off_in_lieu
    0,                                  # remote_non_clinical_tasks
    'Cost of course',                   # cover_education_course
    0,                                  # dedicated_mentorship
    0,                                  # public_recognition
    0,                                  # fast_track_promotion
    0,                                  # access_wellness_programs
    '$500',                             # wellness_reimbursement_3months
    '$500',                             # wellness_reimbursement_6months
    '$500',                             # wellness_reimbursement_12months
    0,                                  # access_relaxation_room
    0,                                  # free_discounted_meals
    '$20 per 5 hours',                  # meal_vouchers_20_per_5hours
    '$10 per hour',                     # transportation_subsidies_10_per_hour
    0,                                  # reserved_parking_space
    0,                                  # access_hospital_car
    'Regular hourly rate',              # overtime_normal_rate
    '1.5x hourly rate',                 # overtime_1_5x_rate
    '2x hourly rate',                   # overtime_2x_rate
    '3x hourly rate',                   # overtime_3x_rate
    0,                                  # department_equipment_upgrades
    0,                                  # access_assistant_aide
    0,                                  # reduced_patient_loads
    0,                                  # priority_access_facilities
    'Equivalent to salary during sabbatical', # paid_sabbatical_3months
    'Equivalent to salary during sabbatical', # paid_sabbatical_6months
    'Equivalent to salary during sabbatical', # paid_sabbatical_12months
    0,                                  # participate_community_initiatives
    0,                                  # additional_paid_breaks
    0,                                  # work_shorter_shifts
    0,                                  # flexible_shift_times
    'One week’s pay',                   # one_time_bonus_1week_pay
    'Three days’ pay',                  # special_bonus_3days_pay
    0,                                  # housing_allowance
    'Portion of utility bills',         # utility_bills_reimbursement
    0,                                  # insurance_coverage
    0,                                  # uniform_equipment_allowance
    '$300',                             # conference_attendance_300
    '$500',                             # conference_attendance_500
    '$700',                             # conference_attendance_700
    0,                                  # mentorship_for_publication
    0,                                  # access_massage_counselling
    0,                                  # lead_improvement_projects
    0,                                  # increased_policy_influence
    0,                                  # guaranteed_time_off_requests
    0,                                  # exclusively_day_shifts
    'One week’s pay',                   # flexible_spending_account
    'One week’s pay',                   # retirement_contribution_1week_pay
    'Equivalent to extra hours worked', # monetary_options_equal_hours
    'Half the extra hours worked',      # monetary_options_half_hours
    0,                                  # personal_development_plan
    0,                                  # recognition_with_memento
    0,                                  # exclusive_access_resources
    'Equivalent monetary value',        # charity_donation_equal_value
    0,                                  # tickets_cultural_event
    'One week’s wages',                 # travel_vouchers_1week_wage
    'Equivalent to extra hours worked', # gift_cards_equal_hours
    '$50 per 5 hours',                  # gift_cards_50_per_5hours
    'Equivalent to extra hours worked', # healthcare_subsidies_equal_hours
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_3months
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_6months
    'Subsidy for tech upgrade',         # tech_upgrade_subsidy_12months
    'One week’s pay',                   # monthly_reward_draw
    'Monetary bonuses at milestones',   # milestone_bonuses
    'One week’s pay',                   # home_office_improvements
    '$300',                             # grant_department_extracurricular_300
    0,                                  # patient_public_thanks
    0,                                  # mentorship_role_junior_staff
    0,                                  # leave_early_fridays_1month
    '$1,000',                           # grant_hospital_library_1000
    '2% salary increase',               # salary_increase_2_percent
    '5% salary increase',               # salary_increase_5_percent
    '10% salary increase',              # salary_increase_10_percent
    '$250',                             # membership_fee_covered_250
    '$200',                             # stipend_uniforms_footwear_200
    0,                                  # establish_legacy_program
    0,                                  # extra_time_with_patients
    '$2,000',                           # nursing_exchange_program_2000
    0,                                  # extend_parental_leave_2weeks
    0,                                  # team_of_month_recognition
    '$1,000',                           # staff_retreat_1000
    'Equivalent to extra hours worked', # sponsorship_fund_patients
    0,                                  # work_life_coaching_1month
    0,                                  # work_life_coaching_3months
    '$3,000',                           # unit_team_building_3000
    0,                                  # reduced_admin_workload
    0,                                  # peer_support_counselling
    0,                                  # access_childcare_facilities
    0,                                  # financial_planning_advice
    'Two weeks’ wages',                 # holiday_package_3months
    'Two weeks’ wages',                 # holiday_package_6months
    'Two weeks’ wages',                 # holiday_package_12months
    0,                                  # personalized_gift
    0,                                  # performance_based_incentives
    'Equivalent to extra hours worked', # deferred_bonus_equal_hours
    0                                   # exchange_admin_for_creative
]

#len(nursing_treatment_ids) == len(nursing_treatment_variations) == len(nursing_treatments_categories) == len(nursing_treatments_numeric_values) == len(nursing_treatments_monetary_values)

# Generate dictionary of lists, pandas dataframe and write to excel file
nurse_dict = {'id': nursing_treatment_ids, 'treatment': nursing_treatment_variations, 'category': nursing_treatments_categories, 'intrinsic_extrinsic_scale': nursing_treatments_numeric_values, 'monetary_value': nursing_treatments_monetary_values}
nurse_df = pd.DataFrame(nurse_dict)
nurse_df.to_excel('./data/inputs/treatment_combinations/nurse_treatments_metadata.xlsx', index=False)

# Define a standardized answer instruction
answer_instruction = "Please write the number of extra hours per week you are willing to work as a numerical value, with a maximum of 2 decimal places."

# Define the output file name
output_filename = "./data/inputs/treatment_combinations/combinations_with_ids_"

# Generate teaching combinations with IDs and save to Excel
generate_combinations_with_ids_to_excel(baseline_scenarios=teaching_scenarios, treatment_variations=teaching_treatment_variations, baseline_prefixes=teaching_scenarios_prefixes, treatment_prefixes=teaching_treatment_ids, answer_instruction=answer_instruction, output_filename=f"{output_filename}teachers.xlsx", treatment_to_baseline_map=None)

# Generate nursing combinations with IDs and save to Excel
generate_combinations_with_ids_to_excel(baseline_scenarios=nursing_scenarios, treatment_variations=nursing_treatment_variations, baseline_prefixes=nursing_scenarios_prefixes, treatment_prefixes=nursing_treatment_ids, answer_instruction=answer_instruction, output_filename=f"{output_filename}nurses.xlsx", treatment_to_baseline_map=None)

##### ------ END OF CODE/SCRIPT FOR PROJECT 1 ------- ####

## ----- Project 2: Actual Usage for Disability & Classic Economic Games Project

## ----- Example Usage

# Define baseline scenarios
baseline_scenarios = ["XXXX", "XXXX"]

# Define short descriptors for baseline scenarios
baseline_prefixes = ["teacher_baseline", "nurse_baseline"]

# Define treatment variations
treatment_variations = [
    "you contributing extra hours would grant you the option to set and manage your daily schedule during regular work hours in the next school term",
    "you would be compensated with additional paid vacation days",
    "you would receive a financial bonus worth two weeks of your salary"
]

# Define short descriptors for treatment variations
treatment_prefixes = ["flexible_hours", "vacation_days", "financial_bonus"]

# Define the treatment to baseline mappings for excluding certain treatment_prefixes from combining with certain baseline_prefixes
treatment_to_baseline_map = {
    "flexible_hours": ["nurse_baseline"],  # Exclude nurses from this treatment
}

# Define a standardized answer instruction
answer_instruction = "Please write the number of extra hours per week you are willing to work as a numerical value, with a maximum of 2 decimal places."

# Define the output file name
output_filename = "./data/inputs/treatment_combinations/combinations_with_ids.xlsx"

# Generate combinations with IDs and save to Excel
generate_combinations_with_ids_to_excel(baseline_scenarios, treatment_variations, baseline_prefixes, treatment_prefixes, answer_instruction, output_filename, treatment_to_baseline_map, joining_text=', considering that')


##### ------ END OF CODE/SCRIPT FOR PROJECT 2 ------- ####