pyramid_numbers = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120, 136, 153, 171, 190, 210, 231, 253, 276, 300]

def decode(message_file):
    subset = []
    message = ''
    for r in message_file:
        if r[0] in pyramid_numbers:
            subset.append(r)

    subset.sort(key=lambda subset: subset[0])

    for r in subset:
        message = message + ' ' + r[1]
        
    return message

message_file = []

file = open('message_file.txt', 'r')
while True:
	content = file.readline()
	if not content:
		break
	message_file.append(content.rstrip('\n').split())

file.close()

for r in message_file:
    r[0] = int(r[0])

print(decode(message_file))








