import pandas as pd
import numpy as np
import datetime
from tqdm.notebook import tqdm
from sklearn.preprocessing import LabelEncoder
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import DataProcessor
dataProcessor = DataProcessor.DataProcessor

class Results(dataProcessor):
    def __init__(self, results):
        super(Results, self).__init__()
        self.data = results
        
    @classmethod
    def read_pickle(cls, path_list):
        df = pd.read_pickle(path_list[0])
        for path in path_list[1:]:
            df = update_data(df, pd.read_pickle(path))
        return cls(df)
    
    @staticmethod
    def scrape(race_id_list):
        """
        レース結果データをスクレイピングする関数

        Parameters:
        ----------
        race_id_list : list
            レースIDのリスト

        Returns:
        ----------
        race_results_df : pandas.DataFrame
            全レース結果データをまとめてDataFrame型にしたもの
        """

        #race_idをkeyにしてDataFrame型を格納
        race_results = {}
        for race_id in race_id_list:
            time.sleep(1)
            try:
                url = "https://db.netkeiba.com/race/" + race_id
                #メインとなるテーブルデータを取得
                df = pd.read_html(url)[0]

                html = requests.get(url)
                html.encoding = "EUC-JP"
                soup = BeautifulSoup(html.text, "html.parser")

                #天候、レースの種類、コースの長さ、馬場の状態、日付をスクレイピング
                texts = (
                    soup.find("div", attrs={"class": "data_intro"}).find_all("p")[0].text
                    + soup.find("div", attrs={"class": "data_intro"}).find_all("p")[1].text
                )
                info = re.findall(r'\w+', texts)
                for text in info:
                    if text in ["芝", "ダート"]:
                        df["race_type"] = [text] * len(df)
                    if "障" in text:
                        df["race_type"] = ["障害"] * len(df)
                    if "m" in text:
                        df["course_len"] = [int(re.findall(r"\d+", text)[-1])] * len(df) #20211212：[0]→[-1]に修正
                    if text in ["良", "稍重", "重", "不良"]:
                        df["ground_state"] = [text] * len(df)
                    if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
                        df["weather"] = [text] * len(df)
                    if "年" in text:
                        df["date"] = [text] * len(df)

                #馬ID、騎手IDをスクレイピング
                horse_id_list = []
                horse_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                    "a", attrs={"href": re.compile("^/horse")}
                )
                for a in horse_a_list:
                    horse_id = re.findall(r"\d+", a["href"])
                    horse_id_list.append(horse_id[0])
                jockey_id_list = []
                jockey_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                    "a", attrs={"href": re.compile("^/jockey")}
                )
                for a in jockey_a_list:
                    jockey_id = re.findall(r"\d+", a["href"])
                    jockey_id_list.append(jockey_id[0])
                df["horse_id"] = horse_id_list
                df["jockey_id"] = jockey_id_list

                #インデックスをrace_idにする
                df.index = [race_id] * len(df)

                race_results[race_id] = df
            #存在しないrace_idを飛ばす
            except IndexError:
                continue
            except AttributeError: #存在しないrace_idでAttributeErrorになるページもあるので追加
                continue
            #wifiの接続が切れた時などでも途中までのデータを返せるようにする
            except Exception as e:
                print(e)
                break
            #Jupyterで停止ボタンを押した時の対処
            except:
                break
        
        #pd.DataFrame型にして一つのデータにまとめる
        race_results_df = pd.concat([race_results[key] for key in race_results])

        return race_results_df
    
    #前処理    
    def preprocessing(self):
        df = self.data.copy()

        # 着順に数字以外の文字列が含まれているものを取り除く
        df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
        df.dropna(subset=['着順'], inplace=True)
        df['着順'] = df['着順'].astype(int)
        df['rank'] = df['着順'].map(lambda x:1 if x<4 else 0)

        # 性齢を性と年齢に分ける
        df["性"] = df["性齢"].map(lambda x: str(x)[0])
        df["年齢"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)

        # 馬体重を体重と体重変化に分ける
        df["体重"] = df["馬体重"].str.split("(", expand=True)[0]
        df["体重変化"] = df["馬体重"].str.split("(", expand=True)[1].str[:-1]
        
        #errors='coerce'で、"計不"など変換できない時に欠損値にする
        df['体重'] = pd.to_numeric(df['体重'], errors='coerce')
        df['体重変化'] = pd.to_numeric(df['体重変化'], errors='coerce')

        # 単勝をfloatに変換
        df["単勝"] = df["単勝"].astype(float)
        # 距離は10の位を切り捨てる
        df["course_len"] = df["course_len"].astype(float) // 100

        # 不要な列を削除
        df.drop(["タイム", "着差", "調教師", "性齢", "馬体重", '馬名', '騎手', '人気', '着順'],
                axis=1, inplace=True)

        df["date"] = pd.to_datetime(df["date"], format="%Y年%m月%d日")
        
        #開催場所
        df['開催'] = df.index.map(lambda x:str(x)[4:6])
        
        #6/6出走数追加
        df['n_horses'] = df.index.map(df.index.value_counts())

        self.data_p = df
    
    #カテゴリ変数の処理
    def process_categorical(self):
        self.le_horse = LabelEncoder().fit(self.data_pe['horse_id'])
        self.le_jockey = LabelEncoder().fit(self.data_pe['jockey_id'])
        super().process_categorical(self.le_horse, self.le_jockey, self.data_pe)
def update_data(old, new):
    """
    Parameters:
    ----------
    old : pandas.DataFrame
        古いデータ
    new : pandas.DataFrame
        新しいデータ
    """

    filtered_old = old[~old.index.isin(new.index)]
    return pd.concat([filtered_old, new])