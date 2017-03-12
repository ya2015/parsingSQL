# simpleSQL.py
#
# simple  using the parsing library to do simple-minded SQL parsing
# could be extended to include where clauses etc.
#
#

from miniDB import *
import sys
import re
import unicodedata
from ppUpdate import Literal, CaselessLiteral, Word, delimitedList, Optional, \
	Combine, Group, alphas, nums, alphanums, ParseException, Forward, oneOf, quotedString, \
	ZeroOrMore, restOfLine, Keyword, upcaseTokens, ParserElement, OneOrMore,alphas8bit, quotedString

def input_file(DB,file):
	with open(file, 'r') as content_file:
		content = content_file.read()
	#print("file:"+content)
	return DB,content
def input_text(DB,sqlText):
	#Eliminate all newline
	#Text = unicodedata.normalize('NFKD', title).encode('ascii','ignore')
	Uans = re.sub(r"\r\n"," ",sqlText)
	#Generate the SQL command respectively
	pattern = re.compile("insert", re.IGNORECASE)
	st = pattern.sub("\ninsert", Uans)
	pattern1 = re.compile("create", re.IGNORECASE)
	st = pattern1.sub("\ncreate", st)
	#Make them into list

	sqlList = [s.strip() for s in st.splitlines()]
	print("sqlList:"+str(sqlList))
	#Call the specific function
	success = []
	errMsg = []
	for obj in sqlList:		
		if str(obj) == "":
			continue
		act = obj.split(' ', 1)[0]
		print("act:"+act)
		print("all:"+obj)
		sucTemp = "" 
		errTemp = ""
		if act.lower()=="create":			
			sucTemp ,errTemp = def_create(DB,obj)
		elif act.lower()=="insert":
			sucTemp ,errTemp = def_insert(DB,obj)
		success.append(sucTemp)
		errMsg.append(errTemp)
	return success, errMsg


def def_create(DB,text):
	createStmt = Forward()
	CREATE = Keyword("create", caseless = True)
	TABLE = Keyword("table",caseless = True)
	PRIMARY = Keyword("PRIMARY KEY", caseless = True)
	INT = Keyword("int", caseless = True)
	VARCHAR = Keyword("varchar", caseless = True)
	#here ident is for table name
	ident	= Word( alphas, alphanums + "_$").setName("identifier")

	#for brackets
	createStmt = Forward()
	varW = Combine(VARCHAR + Optional("("+Word(nums)+")"))

	
	#createExpression << Combine(CREATE + TABLE + ident) + ZeroOrMore()
	tableValueCondition = Group(
		( Word(alphas,alphanums+"_$") + varW + Optional(PRIMARY)) |
		( Word(alphas,alphanums+"_$") + INT + Optional(PRIMARY) )
		)
	#tableValueExpression = Forward()
	#tableValueExpression << tableValueCondition + ZeroOrMore(tableValueExpression) 
	#define the grammar
	createStmt  << ( Group(CREATE + TABLE ) + 
					ident.setResultsName("tables") + 
					Optional( "(" + delimitedList(tableValueCondition).setResultsName("values") + ")", "" ))

	# define Oracle comment format, and ignore them
	simpleSQL = createStmt
	oracleSqlComment = "--" + restOfLine
	simpleSQL.ignore( oracleSqlComment )
	success ,tokens = simpleSQL.runTests(text)
	if(success):
		doubleCheck, flag = process_input_create(DB,tokens)
		return doubleCheck, flag
	else:
		return success, tokens

def def_insert(DB,text):
	print("insert!")
	insertStmt = Forward()
	INSERT = Keyword("insert", caseless = True)
	INTO = Keyword("into",caseless = True)
	VALUES = Keyword("values", caseless = True)
	
	
	columnRval = Word(alphas,alphanums+"_$" ) | quotedString | Word(nums)

	#here ident is for table name
	ident	= Word(alphas, alphanums + "_$").setName("identifier")
	valueCondition = Group(
		 "(" + delimitedList( columnRval ) + ")" 
		)
	valueCondition = delimitedList( columnRval )
		
	#for brackets
	insertStmt = Forward()
	

	#define the grammar
	"""
	insertStmt  << ( Group(INSERT + INTO)  + 
					ident.setResultsName("tables")+
					Optional(valueCondition.setResultsName("col")) +VALUES +
					 valueCondition.setResultsName("val")
					)

	"""

	insertStmt  << ( Group(INSERT + INTO)  + 
					ident.setResultsName("tables")+
					Optional( "(" + delimitedList(valueCondition).setResultsName("col") + ")") +
					VALUES +
					"(" + delimitedList(valueCondition).setResultsName("val") + ")"
					)

	# define Oracle comment format, and ignore them
	simpleSQL = insertStmt
	oracleSqlComment = "--" + restOfLine
	simpleSQL.ignore( oracleSqlComment )
	success, tokens = simpleSQL.runTests(text)

	if(success):
		process_input_insert(DB,tokens)
	else:
		return success, tokens

def process_input_create(DB,tokens):
	keys = []
	col_names = []
	col_datatypes = []
	col_constraints = []
	
	for i in range(len(tokens)):
		try:
			tables = tokens[i]["tables"]
			values = tokens[i]["values"]
		except:
			print("INCORRECT SQL")
			return False, "FAT: VALUES INCORRECT"
		print("table:"+tables)
		print("values:"+str(len(values))+" "+str(values))
		for k in values:
			length = len(k)
			col = k[0]
			typeOri = k[1]
			key = False
			con = None
			if typeOri.lower() != "int":
				con = typeOri[typeOri.find("(")+1:typeOri.find(")")]		
				typeOri = typeOri.split("(",1)[0]
				try:
					con = int(con)
				except:
					return False, "Constraints were not int"
			if length == 3:
				#with primary key, the primary key string should have been checked during parsing
				key = True
			elif length !=2 :
				print("length error")
			
			col_names.append(col)
			col_datatypes.append(typeOri)
			col_constraints.append(con)
			keys.append(key)
		print("tables:"+tables)
		print("col_names:"+str(col_names))
		print("col_datatypes:"+str(col_datatypes))
		print("col_constraints:"+str(col_constraints))
		print("keys:"+str(keys))
		return DB.create_table(tables, col_names, col_datatypes, col_constraints, keys)
		
def process_input_insert(DB,tokens):
	v = []
	c = []
	for i in range(len(tokens)):
		print(str(tokens[i]))
		tables = tokens[i]["tables"]
		#cols = tokens[i]["col"]
		values = tokens[i]["val"]
		print("lenght:"+str(len(values)))
		v.append(values)
		try:
			cols = tokens[i]["col"]		
			print("cols:"+str(cols))	
			#c.append(cols)
		except:
			c = None
			cols = None
			print("no col asssigned")

		print("values:"+str(len(values))+" "+str(values))
		print("table:"+tables)
		print("value:"+str(values))
		print("cols:"+str(cols))
		tableObj = DB.get_table(tables)
		tableObj.insert(v, c)
		return True, None
		
def stage1Test():
	txt = input_file("string.txt")
	print("txt:"+txt)
	input_text(txt)
def testVochar():
	#m = re.search(r"\((0-9+)\)", s)
	while(1):
		st = input()
		num = st[st.find("(")+1:st.find(")")]
		ans = st.split("(",1)[0]
		print (ans)

def test3():
	ans = input_file("string.txt")
	Uans = ans.replace("\n"," ")

	pattern = re.compile("insert", re.IGNORECASE)
	st = pattern.sub("\ninsert", Uans)
	
	tokens = def_insert(st)
	#print(tokens)

def test1():
	ans = input_file("string.txt")
	Uans = ans.replace("\n"," ")
	#s = """\CREATE TABLE Person (person_id int PRIMARY KEY,name varchar(20),gender varchar(1));"""
	
	tokens = def_create(Uans)
	tables = tokens["tables"]
	values = tokens["values"]
	print("table:"+tables)
	print("values:"+str(len(values))+" "+str(values))
	"""
	for ind in tokens:
		print(str(ind))
		print("\n\n\n\n")
	"""
	print(type(tokens[0]))

def test2():
	ans = input_file("string.txt")
	Uans = ans.replace("\n"," ")

	pattern = re.compile("create", re.IGNORECASE)
	st = pattern.sub("\ncreate", Uans)
	
	tokens = def_create(st)
	
	
