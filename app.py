from flask import Flask, jsonify, render_template, request
import pymongo
import datetime
import cfscrape
import re
import time
import pytz
import json
import json_tools


# 新建Flask实例
app = Flask(__name__)

# 新建数据库链接
mongo_client = pymongo.MongoClient("mongodb://literature:yxl981204@leanote-shard-00-00.sxaqe.mongodb.net:27017,leanote-shard-00-01.sxaqe.mongodb.net:27017,leanote-shard-00-02.sxaqe.mongodb.net:27017/myFirstDatabase?ssl=true&replicaSet=atlas-11r758-shard-0&authSource=admin&retryWrites=true&w=majority")

# 判断是否连接成功
# print(mongo_client.server_info())

# 链接数据库，不存在则新建
mongo_db = mongo_client['virmach']

# 链接数据表，不存在则新建
mongo_collection = mongo_db['info']

# 新建scraper实例
scraper = cfscrape.create_scraper()

# 检查数据是否正常
def check_json(input_str):
    try:
        json.loads(input_str)
        return True
    except:
        return False

# 检查数据是否有变化，有变化返回False
def check_update(old_json, new_json):
    if json_tools.diff(old_json,new_json):
        return False
    else:
        return True

# 从官方地址获取抢购信息
def Getinfo():
    # 不在黑五时期的页面信息
    buyinfo = {'date': 'null', 'price': 'null', 'cpu': 0, 'ram': '0', 'hdd': 0, 'bw': 0, 'ips': 0, 'virt': 'null', 'location': 'null', 'win': 'null', 'message': 'null',"ended":"已结束", 'url': ''}
    old_data = 'Please only have one black friday page open at any given time, and if you are on a third party website ensure that you are not having it refreshed too often in the background'

    old_json = scraper.get("https://vkceyugu.cdn.bspapp.com/VKCEYUGU-6cc46a21-10af-4cd7-a52d-d8c57329708e/53c2e3fe-6438-47ca-bb8c-3cc976dd8a7e.json").content

    #web_data = scraper.get("https://www.ovzv.cn/new_plan.json").content
    web_data = scraper.get("https://billing.virmach.com/modules/addons/blackfriday/new_plan.json").content

    if(web_data != old_data):
        if check_json(web_data):
            data_test = json.loads(web_data)
            if('ended' in data_test):
                del data_test["ended"]
                data_test["ended"] = "已售罄"
                data_test["url"] = 'https://billing.virmach.com/cart.php?a=add&pid=' + str(data_test['pid']) + '&billingcycle=annually'
                buyinfo = data_test

                return getdata(buyinfo)
            else:
                with open("./old.json","r") as f:
                    s = json.load(f)
                    user_dict = json.loads(s)
                    if check_update(json.loads(old_json), json.loads(web_data)):
                        # print("没变哈，持续销售中")
                        old_json = web_data
                        buyinfo = json.loads(web_data)
                        buyinfo["url"] = 'https://billing.virmach.com/cart.php?a=add&pid=' + str(buyinfo['pid']) + '&billingcycle=annually'
                        buyinfo["ended"] = "销售中"
                        return getdata(buyinfo)
                    else :
                        # print("更新了，快买")
                        old_json = web_data
                        buyinfo = json.loads(web_data)
                        buyinfo["url"] = 'https://billing.virmach.com/cart.php?a=add&pid=' + str(buyinfo['pid']) + '&billingcycle=annually'
                        buyinfo["ended"] = "销售中"
                        with open("./old.json","w") as f:
                            s = json.dumps(getdata(buyinfo))
                            json.dump(s,f)
                        # insert(data)
                        return getdata(buyinfo)
    else:
        return buyinfo

# 查询数据库中的数据
def findAll():
    list   = []
    cur = mongo_collection.find()
    for i in cur:
        del i["_id"]
        list.append(i)
    # 返回去除_id字段的数组数据
    return list[::-1]


def getdata(data):
    info = {
        'price' : re.findall(r"\d+\.?\d*",data['price'])[0],
        'cpu' : data['cpu'],
        'ram' : data['ram'],
        'hdd' : data['hdd'],
        'bw' : data['bw'],
        'ips' : data['ips'],
        'virt' : data['virt'],
        'location' : data['location'],
        'win' : data['windows'],
        'message' : data['message'],
        'ended' : data['ended'],
        'url' : 'https://billing.virmach.com/cart.php?a=add&pid=' + str(data['pid']) + '&billingcycle=annually'
 
    }
    return info

# 向数据库中插入数据
def insert(info):
    del info["ended"]
    mongo_collection.insert_one(info)

    
#翻译页面路由配置
@app.route('/buyjson', methods=['GET'])
def buyjson():
    # 返回单条数据
    return jsonify(Getinfo())

#翻译页面路由配置
@app.route('/historyjson', methods=['GET'])
def historyjson():
    # 返回Json数组
    return jsonify(findAll())

@app.route('/')
def index():
    
    activity_data = {'date': '2021-09-21 10:19:08', 'price': '47.67', 'cpu': 3, 'ram': '11264', 'hdd': 25, 'bw': 22000, 'ips': 1, 'virt': 'KVM', 'location': 'BUFFALO, NY', 'win': 'FALSE', 'message': '1 GIGABIT', 'url': 'https://billing.virmach.com/cart.php?a=add&pid=179&billingcycle=annually'}
    return render_template('index.html', a_data = activity_data)


if __name__ == '__main__':
    # app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    # for heroku
    app.run(debug=True)