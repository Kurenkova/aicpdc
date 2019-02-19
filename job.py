import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="aic",
  passwd="pdc",
  database="aicpdc"
)

mycursor = mydb.cursor()
mycursor.execute("DELETE FROM all_persons");
sql = """SELECT *             запрос
FROM
(SELECT users_discount_cards.PCardInd as dc_PID, users_discount_cards.Age as dc_age, users_discount_cards.email AS dc_email, users_discount_cards.civility AS dc_civility, DATEDIFF(MAX(shop_check_data.Purchase_time), MIN(shop_check_data.Purchase_time)) AS dc_days, AVG(shop_check_data.Purchase_price) AS dc_avg
FROM users_discount_cards, shop_check_data
WHERE shop_check_data.CardInd IS NOT NULL
AND shop_check_data.CardInd = users_discount_cards.CardInd
GROUP BY dc_PID) dc JOIN
(SELECT PBankCardInd AS bc_PID, Civility AS bc_civility, Age AS bc_age, Email AS bc_email, Money_month as bc_avg
FROM users_bank_cards) bc
ON dc.dc_age = bc.bc_age AND dc.dc_civility = bc.bc_civility AND dc.dc_email = bc.bc_email
GROUP BY bc.bc_PID;"""
mycursor.execute(sql)
myresult = mycursor.fetchall()
for r in myresult:
	sql = 'INSERT INTO all_persons(civility, age, email, money_month, money_month_dc, dcId, bcId) VALUES("' + r[3] + '", ' + str(r[1]) + ', "' + r[2] + '", ' + str(r[10]) + ', ' + str(float(r[5])/((float(r[4])+1)/30)) + ', ' + str(r[0]) + ', ' + str(r[6]) + ')'
	mycursor.execute(sql)
	mydb.commit()
#Добавление пользователей, платящих только картой лояльности
discount_cards = []
mycursor.execute("SELECT dcId FROM all_persons")
myresult = mycursor.fetchall()
for r in myresult:
	discount_cards.append(r[0])
sql = """SELECT users_discount_cards.PCardInd as dc_PID, users_discount_cards.Age as dc_age, users_discount_cards.email AS dc_email, users_discount_cards.civility AS dc_civility, DATEDIFF(MAX(shop_check_data.Purchase_time), MIN(shop_check_data.Purchase_time)) AS dc_days, AVG(shop_check_data.Purchase_price) AS dc_avg
FROM users_discount_cards, shop_check_data
WHERE shop_check_data.CardInd IS NOT NULL
AND shop_check_data.CardInd = users_discount_cards.CardInd
GROUP BY dc_PID"""
mycursor.execute(sql)
myresult = mycursor.fetchall()
for r in myresult:
	if not (r[0] in discount_cards):
		try:
			sql = 'INSERT INTO all_persons(civility, age, email, money_month, money_month_dc, dcId) VALUES("' + r[3] + '", ' + str(r[1]) + ', "' + r[2] + '", ' + str(0) + ', ' + str(float(r[5])/((float(r[4])+1)/30)) + ', ' + str(r[0]) + ')'
			mycursor.execute(sql)
		except:
			print("Incorect database record")
mydb.commit()
#Добавление пользователей, платящих только банковскими картами
bank_cards = []
mycursor.execute("SELECT bcId FROM all_persons")
myresult = mycursor.fetchall()
for r in myresult:
	bank_cards.append(r[0])
sql = """ SELECT PBankCardInd AS bc_PID, Civility AS bc_civility, Age AS bc_age, Email AS bc_email, Money_month as bc_avg
FROM users_bank_cards """
mycursor.execute(sql)
myresult = mycursor.fetchall()
for r in myresult:
	if not (r[0] in bank_cards):
		try:
			sql = 'INSERT INTO all_persons(civility, age, email, money_month, money_month_dc, bcId) VALUES("' + r[1] + '", ' + str(r[2]) + ', "' + r[3] + '", ' + str(r[4]) + ', ' + str(0) + ', ' + str(r[0]) + ')'
			mycursor.execute(sql)
		except:
			print("Incorect database record")
mydb.commit()
mydb.close()
