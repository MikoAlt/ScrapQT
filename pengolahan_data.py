import numpy as np
import pandas as pd
import sqlite3
from scipy import stats


class DataSortingScrapper:
    def __init__(self, search: str):
        self.search = search

    def data_frame(self):
        conn = sqlite3.connect('')  # nama filenya
        sql_query = 'SELECT column1, column2 FROM table_name'
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df  # ini juga disesuaikan dari ecommerce, harga, dan barang y ang di search oleh user5

    def cleaning_ecommerce(self):
        df = self.data_frame()
        managers = []  # diganti dengan ecommerce nanti
        for index in range(len(df['Manager'])):  # ini juga diganti nanti
            NotFixMangers = df['Manager'][index].split()
            new_managers = " ".join(NotFixMangers)
            managers.append(new_managers)
        return managers

    def fix_ecommerces(self):
        fix_managers = self.cleaning_ecommerce()
        set_managers = set(fix_managers)
        return np.array(list(set_managers))  # ganti dengna ecommerces nanti

    def manage_price(self):
        df = self.data_frame()
        fix_ecommrces = self.fix_ecommerces()
        all_ecommerces = self.cleaning_ecommerce()
        prod_name = self.search.lower()
        dict_price = {}
        for i, val in enumerate(df['Product']):
            if prod_name in val.lower():
                current_ecommerce = all_ecommerces[i]
                if current_ecommerce in fix_ecommrces:
                    if current_ecommerce in dict_price:
                        dict_price[current_ecommerce].append(df['Quantity'][i])
                    else:
                        dict_price[current_ecommerce] = [df['Quantity'][i]]

        return dict_price

    def bar_data(self):
        data_price = self.manage_price()
        e_commerces = list(data_price.keys())

        #Pemisahan Mode Median dan Mean
        means = [np.mean(prices) for prices in data_price.values()]
        medians = [np.median(prices) for prices in data_price.values()]
        modes = [stats.mode(prices) for prices in data_price.values()]

        return e_commerces, means, medians, modes
