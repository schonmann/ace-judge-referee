from main.models import Usuario

def text_account_handler(inputfile):
	infile = open(str(inputfile), 'r')
	string = infile.readline()
	cont = 0
	field_cont = 0
	s = ''
	nome = ''
	email = ''
	senha = ''
	us = ''
	stringb = ''
	while string != '':
		for i in string:
			if i == ',':
				cont += 1
			elif cont==1:
				stringb += s
				print 'stringb: ' + stringb
				if field_cont == 0:
					us = stringb
					field_cont += 1
				elif field_cont == 1:
					nome = stringb
					field_cont += 1
				elif field_cont == 2:
					email = stringb
					field_cont += 1
				stringb = ''
				s = ''
				cont += 1
			elif cont==2 or cont==0:
				s += i
				cont = 0
		senha = s
		p = Usuario(username = us, name = nome, email = email, password = senha, user_type = 'AL')
		p.save()
		s = ''
		nome = ''
		email = ''
		senha = ''
		us = ''
		stringb = ''
		cont = 0
		field_cont = 0
		string = infile.readline()

def handle_uploaded_file(f):
    fp = open('/home/pedro/tech.txt', 'wb+')
    for chunk in f.chunks():
         fp.write(chunk)
    fp.flush()
    fp.close()
