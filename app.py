# -*- coding: utf-8 -*-
from re import A

from unittest import result
from flask import Flask, render_template, request, jsonify
import DataProcessor
dataProcessor = DataProcessor.DataProcessor
import Results
result = Results.Results(dataProcessor)
import HorseResults
horseResults = HorseResults.HorseResults
import pandas as pd
import Return
import Peds
peds = Peds.Peds
returnp = Return.Return
import ShutubaTable
shutubaTable = ShutubaTable.ShutubaTable(dataProcessor)
import GetRaceId
getRaceId = GetRaceId.GetRaceId

import json



app = Flask(__name__)

@app.route('/')
def index():
    #目的変数は「3着以内に入ったかどうか」の0or1データを持った'rank'
    X = r.data_c.drop(['rank', 'date', '単勝'], axis=1)
    y = r.data_c['rank']

    #optunaによってチューニングされたLightGBMのパラメータ
    params = {
        'objective': 'binary',
        'random_state': 100,
        'feature_pre_filter': False,
        'lambda_l1': 4.693572572985162e-07,
        'lambda_l2': 0.8052948126650886,
        'num_leaves': 5,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.9783720284106503,
        'bagging_freq': 7,
        'min_child_samples': 50
    }

    #LightGBMによる訓練
    lgb_clf = lgb.LGBMClassifier(**params)
    lgb_clf.fit(X.values, y.values)

    #自作したModelEvaluatorクラスのオブジェクトを作成
    me = ModelEvaluator(lgb_clf, ['return_tables.pickle'])
    return json.dumps("st", indent=4, ensure_ascii=False)





#指定した日のレース情報を取得する
@app.route("/scrape", methods=["GET"])
def get_user():
    req = request.args
    day = req.get("days") 
    race_id_list = getRaceId.scrape(day)
    st = result.scrape(race_id_list).values.tolist()
    return json.dumps(st, indent=4, ensure_ascii=False)


#馬の過去成績データ
@app.route("/horseResults", methods=["GET"])
def get_user():
    req = request.args
    day = req.get("days") 
    results = pd.read_pickle('results.pickle')
    horse_id_list = results['horse_id'].unique()
    horse_results = horseResults.scrape(horse_id_list).values.tolist()
    return json.dumps(horse_results, indent=4, ensure_ascii=False)

#馬の血統データ
@app.route("/peds", methods=["GET"])
def get_user():
    req = request.args
    day = req.get("days") 
    results = pd.read_pickle('results.pickle')
    horse_id_list = results['horse_id'].unique()
    horse_results = peds.scrape(horse_id_list).values.tolist()
    return json.dumps(horse_results, indent=4, ensure_ascii=False)




#当日のレース情報を取得する
@app.route("/scrape", methods=["GET"])
def get_user():
    req = request.args
    day = req.get("days") 
    race_id_list = getRaceId.scrape(day)
    st = shutubaTable.scrape(race_id_list, day)
    return json.dumps(st, indent=4, ensure_ascii=False)






if __name__ == '__main__':
	app.run()




