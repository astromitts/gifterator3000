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

