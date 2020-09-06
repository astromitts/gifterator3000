from giftexchange.models import AppUser, Participant

def csv_lines_to_dict(expected_header, lines):
	parsed_lines = []
	line_index = 0
	clean_lines = [line.strip() for line in lines]
	for line in clean_lines:
		parts = line.split(',')
		if line_index == 0:
			header_positions = {}
			header_index = 0
			for part in parts:
				if part in expected_header:
					header_positions[part] = header_index
				header_index += 1
		else:
			parsed_line = {}
			for field in expected_header:
				parsed_line[field] = parts[header_positions[field]]
			parsed_lines.append(parsed_line)
		line_index += 1
	return parsed_lines


def save_parsed_participants_as_appusers(parsed_participants):
	appusers = []
	error_rows = []
	for participant in parsed_participants:
		djangouser, created_djangouser = AppUser.get_or_create_djangouser(
			first_name=participant['first_name'],
			last_name=participant['last_name'],
			email=participant['email']
		)
		appuser, created_appuser = AppUser.get_or_create(djangouser)
		appusers.append(appuser)
	return appusers
