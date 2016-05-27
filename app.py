# coding: utf-8

from datetime import datetime
from flask import Flask
from flask import render_template
from flask import request
import time
from views.todos import todos_view
from leancloud import Object
from leancloud import Query
from flask import request
from flask import jsonify
from flask import session,make_response,redirect
from leancloud import User
import paho.mqtt.publish as publish
import json

app = Flask(__name__)
app.secret_key='afjlsjfowflajflkajfkjfkaljf'
class test_esp(Object):
	pass
class DeviceKey(Object):
	pass
class Device:
	index = 0
	time  = ""
	def __init__(self,index,time):
		self.index =index
		self.time  =time

# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


@app.route('/')
def index():
	username =request.cookies.get('username')
	islogin = session.get('islogin')
	print username, ' ',islogin
	if (not username) or( not islogin ) :
		username = u'请先登录'
		islogin = '0'
	return render_template('index.html',username =username,islogin=islogin)
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		username = 	request.form.get('username')
		password =	request.form.get('password')
		try:
			User().login(username, password)
			response = make_response(redirect('/'))
			response.set_cookie('username',value = username,max_age =300)
			session['islogin'] = '1'
			print 'login succeed'
			return response
		except Exception,e:
		    
			print e 
			session['islogin']='0'
			return redirect('/login')
	else:
		session['islogin'] ='0'
		return render_template('login.html')
		
@app.route('/ping/<key>')
def ping(key):
	ping_time =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	try:
		query = Query(DeviceKey)
		device=query.get(key)
		index = device.get('index')
		device.set('ping_time',ping_time)
	except:
		return jsonify(error ='search error')
	try:
		device.save()
	except:
		return jsonify(error ='save error')
	print 'device ',index,'ping @',ping_time
	return jsonify(index=index,time =ping_time)
@app.route('/time')
def time_now():
	now_time 	=  datetime.now()
	timestamp    =  time.time()
	return jsonify(time = now_time,timestamp = timestamp)
@app.route('/control/<int:speed>')
def testmatt(speed):
	#print 'control send',speed
	#publish.single("mqtt", "hello leancloud", hostname="s.vvlogic.com")
	#publish.single("E-5CCF7F800EB6/fanspeed", speed, hostname="v.vvlogic.com",port=9001,auth = {'username':"vv", 'password':"vv"})
	control_speed(speed)
	return 'send contrl ok!'
@app.route('/tem',methods=['POST'])
def tem():
	tem_data = request.json['tem']
	test_data = test_esp(tem=tem_data)
	test_data.save()
	return 'measure,successed!'
@app.route('/devicekey')
def deviceKey():
	device_key 	= DeviceKey()
	try:
		device_key.save()
	except:
		jsonify(error='save')
	device_id 	= device_key.id
	create_date 	= device_key.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
	return jsonify(key=device_id,createdAt=create_date)
def get_latest(key):
	try:
		query =Query(test_esp)
		query.equal_to('key',key)
		query.descending('createdAt')
		latest = query.first()
		return latest
	except:
		rasie 
@app.route('/latest')
def latest():
	key=request.headers.get('key')
	if(key==None):
		return jsonify(error='No key in Header')
	try:
		data=get_latest(key)
	except:
		return jsonify(error='invalid key')
	try:
		tem	=data.get('t')
		hum 	=data.get('h')
		nosie   =data.get('noise')
		pm	=data.get('pm')
		ch2o	=data.get('ch2o')
		created_at = data.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")	
        	return jsonify(key = key,tem=tem,hum=hum,noise=nosie,pm=pm,ch2o=ch2o,createdAt=created_at)
	except:
		return jsonify(error='Get Error')

@app.route('/latest/<key>')
def latest_key(key):
	print 'get latest result for ',key
	try:
		data=get_latest(key)
	except:
		return jsonify(error='invalid key')
	try:
		tem	=data.get('t')
		hum 	=data.get('h')
		nosie   =data.get('noise')
		pm	=data.get('pm')
		ch2o	=data.get('ch2o')
		created_at = data.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")	
        	return jsonify(key = key,tem=tem,hum=hum,noise=nosie,pm=pm,ch2o=ch2o,createdAt=created_at)
	except:
		return jsonify(error='Get Error')
#html for result view
@app.route('/result/<key>')
def result(key):
	print 'get result from key',key
	try:
		data=get_latest(key)
	        hour=data.created_at.hour+8
		ch2o = data.get('ch2o')
		if ch2o ==65535:
			ch2o=0
		ch2o =round(ch2o*1.32/1000,2)
		data.set('ch2o',ch2o)
	except:
		return jsonify(error='invalid key')
	try:
		local_time=utc2local(data.created_at)
	except:
		print 'local time change error'
		local_time = data.created_at
	return render_template('result.html', esp_test=data,local_time=local_time)
	
#get devices status
@app.route('/status')
def device_status():
		try:
			query =Query(DeviceKey)
			query.ascending('index')
			devices =query.find()
		except:
			jsonify(status='find error')
		return  render_template('status.html',devices=devices)
@app.route('/test/<key>')
def test(key):
	query = Query(DeviceKey)
	device=query.get(key)
	index = device.get('index')
	name  = device.get('name')
	print 'Add Data',index,name
	upload_time =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	device.set('uploadtime',upload_time)
	device.save()
	print index,'save at',upload_time
	return	jsonify(status='ok')
@app.route('/changename/<int:index>',methods=['GET','POST'])
def change_name(index):
	if request.method == 'POST':
		name_cn = 	request.form.get('name_cn');
		if(name_cn==''):
			name_cn = None
		query =Query(DeviceKey)
		query.equal_to('index',index)
		devicekey=query.first()
		devicekey.set('name_cn',name_cn)
		devicekey.save()
		return redirect('/status')
	else:
		return render_template('changename.html')
#html for result view
@app.route('/resultindex/<int:index>')
def result_index(index):
	print 'get result from index',index
	try:
		query =Query(DeviceKey)
		query.equal_to('index',index)
		devicekey=query.first()
		device_name = devicekey.get('name_cn')
		key=devicekey.id
	except:
		return jsonify(error='invalid index')
	try:
		data=get_latest(key)
		hour=data.created_at.hour+8
		ch2o = data.get('ch2o')
		if ch2o ==65535:
			ch2o=0
		ch2o =round(ch2o*1.32/1000,2)
		data.set('ch2o',ch2o)
	except:
		return jsonify(error='invalid key')
	try:
		local_time=utc2local(data.created_at)
	except:
		print 'local time change error'
		local_time = data.created_a
	#pm =average_pm(24,key)
	pm =min_pm(key)
	noise = min_noise(key)
	return render_template('result.html', esp_test=data,local_time=local_time,pm=pm,noise=noise,index=index,device_name = device_name)
def min_pm(key):
	query =Query(test_esp)
	query.equal_to('key',key)
	query.descending('createdAt')
	pm=[]
	query.limit(60)
	results = query.find()
	for result in results:
		pm.append(result.get('pm'))
	pm.reverse()
	return pm
def min_noise(key):
	query =Query(test_esp)
	query.equal_to('key',key)
	query.descending('createdAt')
	noise=[]
	query.limit(60)
	results = query.find()
	for result in results:
		noise.append(result.get('noise'))
	noise.reverse()
	return noise	
def average_pm(num,key):
	query =Query(test_esp)
	query.equal_to('key',key)
	query.descending('createdAt')
	pm=[]
	for i in range(1,24):
		query.limit(60)
		results = query.find()
		pm.append(average(results,60))
		query.skip(60*i)
	pm.reverse()
	print pm
	return pm
def average(results,len):
	pm_min   =[]
	for result in results:
		pm_min.append(result.get('pm'))
	return sum(pm_min)/len
def utc2local(utc_st):
	try:
		local_time = datetime.now()
		utc_time = datetime.utcnow()
		offset =local_time - utc_time
		local_st = utc_st +offset
		return local_st 
	except:
		print 'time change error'
		raise
@app.route('/jsonindex/<int:index>')
def json_index(index):
	print 'get result from index',index
	try:
		query =Query(DeviceKey)
		query.equal_to('index',index)
		devicekey=query.first()
		key=devicekey.id
		lat = devicekey.get('lat')
		lng = devicekey.get('lng')
	except:
		return jsonify(error='invalid index')
	try:
		data=get_latest(key)
	except:
		return jsonify(error='no data',key=key)
	ch2o = data.get('ch2o')
	if ch2o ==65535:
			ch2o=0
	ch2o =round(ch2o*1.32/1000,2)
	data.set('ch2o',ch2o)
	tem	=round(data.get('t')/10.0-40.0,1)
	hum 	=data.get('h')
	nosie   =data.get('noise')
	pm	=data.get('pm')
	ch2o	=data.get('ch2o')
	return jsonify(key = key,tem=tem,hum=hum,noise=nosie,pm=pm,ch2o=ch2o,createdAt=data.created_at,index=index,heze_rate= 80,tem_od=23.3,hum_od=12,pm_od=100,longitude=lng,latitude=lat)
@app.route('/add', methods=['POST'])
def add():
	try:
		key_data = request.json['key']
		ch2o_data= request.json['ch2o']
		tem_data = request.json['tem']
		hum_data = request.json['hum']
		noi_data = request.json['noise']
		pm_data  = request.json['pm']
	except:
		return jsonify(error='json')
	query = Query(DeviceKey)
	try:
		device=query.get(key_data)
		index = device.get('index')
		name  = device.get('name')
		print 'Add Data',index,name
		control(index,pm_data)
		test_data = test_esp(ch2o=ch2o_data, t=tem_data, h=hum_data, noise=noi_data, pm=pm_data, key=key_data,name=name,index =index)
		try:
			test_data.save()
			
		except:
			return jsonify(error='save')
		upload_time =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		device.set('uploadtime',upload_time)
		try:
			device.save()
			print index,'save at',upload_time
		except:
			return jsonify(error ='staus save error')
		return jsonify(status ='succeed')
	except:
		return jsonify(error = 'key')
@app.route('/upload', methods=['POST'])
def upload():
	try:
		key_data = request.json['key']
		query = Query(DeviceKey)
		device=query.get(key_data)
		index = device.get('index')
		name  = device.get('name')
		print 'upload',index,name
	except:
		return jsonify(error = 'key')
	try:
		datas = request.json['data']
		for data in datas:
			print 'tem',data['tem']
			print 'time',data['time']
	except:
	   return jsonify(error = 'json')
	return jsonify(status ='succeed')
def push_mqtt(speed):
	print 'send control ',speed
	#sn= 71c064f1e0828966
	control_dict ={}
	control_dict['fanspeed'] =speed
	control_dict['led'] =0
	control_dict['autoupdate'] =0
	control_dict['upurl'] =""
	control_dict['suburl'] =""
	control_json = json.JSONEncoder().encode(control_dict)
	#publish.single("71c064f1e0828966/fanspeed", speed, hostname="v.vvlogic.com",port=9001,auth = {'username':"vv", 'password':"vv"})
	print control_json
	publish.single("71c064f1e0828966/rx", control_json, qos=0,retain=False,hostname="v.vvlogic.com",port=9001,auth = {'username':"vv", 'password':"vv"})
def control(index,pm):
	if index ==1:
		speed=int(pm/10)
		if speed >30:
			speed =30
		push_mqtt(speed)
def control_speed(speed):
		if speed >30:
			speed =30
		push_mqtt(speed)


	

