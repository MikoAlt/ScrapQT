import numpy as np
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy import stats



class DataSortingScrapper:
    def __init__(self, search: str):
        self.search = search

    def data_frame(self):
        conn = sqlite3.connect('data/scraped_data.db')  # nama filenya
        sql_query = "SELECT title, price, ecommerce FROM products"
        df = pd.read_sql_query(sql_query, conn)
        df_cleaned = df.dropna(subset=['title', 'ecommerce'])
        df_reset = df_cleaned.reset_index(drop= True)
        conn.close()
        return df_reset  # ini juga disesuaikan dari ecommerce, harga, dan barang y ang di search oleh user5

    def cleaning_ecommerce(self):
        df = self.data_frame()
        managers = []  # diganti dengan ecommerce nanti
        for index, val in enumerate(df['ecommerce']):  # ini juga diganti nanti
            try:
                NotFixMangers = df['ecommerce'][index].split()
            except AttributeError:
                print(f"There is a blank list in the column of row{index}")
            else:
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
        for i, val in enumerate(df['title']):
            try:
                if prod_name in val.lower():
                    try:
                        current_ecommerce = all_ecommerces[i]
                        if current_ecommerce in fix_ecommrces:
                            if current_ecommerce in dict_price:
                                dict_price[current_ecommerce].append(df['price'][i])
                            else:
                                dict_price[current_ecommerce] = [df['price'][i]]
                    except IndexError:
                        print(f'Index out of range')
            except AttributeError:
                print(f'There is a none in index {i}')

        return dict_price

    def bar_data(self):
        data_price = self.manage_price()
        e_commerces = list(data_price.keys())

        #Pemisahan Mode Median dan Mean
        means = [np.mean(prices) for prices in data_price.values()]
        medians = [np.median(prices) for prices in data_price.values()]
        modes = [stats.mode(prices, keepdims=False).mode for prices in data_price.values()]

        return e_commerces, means, medians, modes

    def bar_chart(self):
        csfont = {'fontname': 'Sans Serif'}
        if not self.manage_price():
            return None
        e_commerces, means, medians, modes = self.bar_data()
        x = np.arange(len(e_commerces))
        width = 0.25

        # Plotting
        fig, ax = plt.subplots(figsize=[16, 9])
        ax.bar(x - width, means, width, label='Mean', color='#0059FF')
        ax.bar(x, medians, width, label='Median', color='#FFD400')
        ax.bar(x + width, modes, width, label='Mode', color='#4AD991')

        # Tambahkan teks, judul, dan label
        ax.set_ylabel('Harga (Rupiah)', fontsize=12)
        ax.set_title(f'Perbandingan Statistik Harga untuk "{self.search}"', fontsize=20, **csfont)
        ax.set_xticks(x)
        ax.set_xticklabels(e_commerces, fontsize=12, rotation=45, ha='center')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.8)
        ax.set_frame_on(False)

        fig.tight_layout()
        plt.legend()

        return fig

    def box_plot(self):
        price_data = self.manage_price()
        if not price_data:
            return None

        ecommerces = list(price_data.keys())
        price_lists = list(price_data.values())
        x = np.arange(len(ecommerces))

        fig, ax = plt.subplots(figsize=[16, 9])
        bplot = ax.boxplot(price_lists, positions=x + 0.1, labels=ecommerces, patch_artist=True, vert=True, widths=0.25)

        for i, prices in enumerate(price_lists):
            x_jitter = np.random.normal(x[i] - 0.2, 0.03, size=len(prices))
            ax.scatter(x_jitter, prices, alpha=0.7, s=25, color='darkblue')

        ax.set_title(f'Distribusi Harga untuk "{self.search}"', fontsize=20)
        ax.set_ylabel('Harga (Rupiah)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(ecommerces, fontsize=12, rotation=45, ha='center')
        ax.grid(axis='y', linestyle='--', alpha=0.8)
        ax.set_frame_on(False)

        colors = cm.Set1(np.linspace(0, 1, len(ecommerces)))
        for patch, color in zip(bplot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        fig.tight_layout()
        return fig

if __name__ == '__main__':
    search = input('Testing: ')
    data = DataSortingScrapper(search)
    data.bar_chart()
    data.box_plot()
    plt.show()
