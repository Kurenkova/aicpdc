#импорт Flask
from flask import Flask, request, render_template, url_for
#импорт коннектора MySQL
import mysql.connector
#импорт библиотеки машинного обучения
from sklearn.cluster import KMeans
#импорт numpy - библиотеки для работы с массивами
import numpy as np
#для "сортировки" словаря
import operator
#для рассылки по электронной почте
from flask_mail import Mail, Message

app = Flask(__name__)
mail = Mail(app)

mydb = mysql.connector.connect(
  host="localhost",
  user="aic",
  passwd="pdc",
  database="aicpdc"
)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'kurenkovadsh@gmail.com'
app.config['MAIL_PASSWORD'] = '*****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


@app.route('/')
def hello_world():
	return render_template('index.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
	if request.method == 'POST':
		#обработка данных с формы
		result = request.form
		groups_count = int(result['groups_count'])
		items_count = int(result['items_count'])
		date_from = result['date_from']
		date_to = result['date_to']
		print(groups_count)
		print(items_count)
		print(date_from)
		print(date_to)
		#выбор данных для обучения модели
		mycursor = mydb.cursor()
		mycursor.execute("SELECT Age, money_month, money_month_dc FROM all_persons")
		myresult = mycursor.fetchall()
		all_data = []
		for r in myresult:
			row_data = [float(r[0]), float(r[1]), float(r[2])]
			all_data.append(row_data)
		X = np.array(all_data)
		#кластеризация покупателей
		model = KMeans(n_clusters=groups_count)
		model.fit(X)
		clusters = model.predict(X)
		mycursor.execute("SELECT PInd FROM all_persons")
		myresult = mycursor.fetchall()
		persons = []
		for r in myresult:
			persons.append(r[0])
		for p, g in zip(persons, clusters):
			sql = 'UPDATE all_persons SET PGroup = ' + str(g) + ' WHERE PInd = ' + str(p)
			mycursor.execute(sql)
		mydb.commit()
		mycursor.execute("SELECT PGroup, PInd FROM all_persons ORDER BY PGroup")
		myresult = mycursor.fetchall()
		table_data = []
		table_data.append([])
		gr = 0
		for r in myresult:
			if gr == r[0]:
				table_data[gr].append(r[1])
			else:
				gr = r[0]
				table_data.append([])
		#Определяем спрос на товары по группам:
		sql = """SELECT all_persons.PGroup, goods_shop_check_data.Goods_article, goods_shop_check_data.Goods_name, shop_check_data.BankCardInd, shop_check_data.CardInd
				FROM all_persons, goods_shop_check_data JOIN shop_check_data 
				ON goods_shop_check_data.CheckInd = shop_check_data.CheckInd
				WHERE all_persons.bcId = shop_check_data.BankCardInd OR all_persons.dcId = shop_check_data.CardInd
				ORDER BY all_persons.PGroup"""
		mycursor.execute(sql)
		myresult = mycursor.fetchall()
		goods_data = []
		ind = 0
		i = 0
		g_dict = {}
		while i < len(myresult):
			if (myresult[i][0] == ind):
				if myresult[i][2] in g_dict:
					n_v = g_dict[myresult[i][2]] + 1
					g_dict.update({myresult[i][2]: n_v})
				else: 
					g_dict.update({myresult[i][2]: 1})
				i = i + 1
			else:
				goods_data.append(g_dict)
				if (int(myresult[i][0]) - ind > 1):
					while int(myresult[i][0]) - ind > 1:
						goods_data.append(g_dict)
						ind = ind+1
						g_dict = {"нет рекомендуемых товаров": 0}
				goods_data.append(g_dict)
				ind = myresult[i][0]
				g_dict = {}
		goods_data.append(g_dict)
		#Отбираем товары по количеству (не больше, чем мы указали)
		goods_lists = []
		for r in goods_data:
			goods_list = []
			sorted_list = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
			for i in sorted_list:
				goods_list.append(i[0])
			final_list = goods_list[0:min(len(goods_list), items_count)]
			goods_lists.append(final_list)
		#Рассылка по электронной почте
		mycursor.execute("SELECT PGroup, Email FROM all_persons WHERE Email IS NOT NULL")
		myresult = mycursor.fetchall()
		for r in myresult:
			if ("нет рекомендуемых товаров" not in goods_lists[r[0]]):
				try:
					msg = Message('Рекомендации товаров только для Вас!', sender = 'Магазин АИС ПДС', recipients = [str(r[1])])
					msg.body = "Рекомендуем приобрести следующие товары по эксклюзивным ценам: " + ", ".join(goods_lists[r[0]])
					#mail.send(msg)
				except:
					print('Error sending emial to recipient ' + str(r[1]))
		#Готовим данные для отображения
		groups_data = []
		for i in range(len(table_data)):
			obj = {'ind': i, 'g_size': len(table_data[i]), 'goods': ", ".join(goods_lists[i])}
			groups_data.append(obj)
		return render_template("result.html", persons = table_data, groups_data = groups_data)
	if request.method == 'GET':
		mycursor = mydb.cursor()
		mycursor.execute("SELECT * FROM banks")
		myresult = mycursor.fetchall()
		return render_template("result.html", banks = myresult)


@app.route('/neznayu')
def davaitevypridymaete():
	if request.method == 'GET':
		uchenick = {'kluch': 'znachenie'}
		return render_template("result.html", moi_slovar=uchenick)




app.run(debug=True, host='0.0.0.0', port=3000)
