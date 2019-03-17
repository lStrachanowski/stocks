import requests
import zipfile
import os
from flask import Flask, flash
from flask import render_template, request, redirect,url_for
import pandas as pd
import plotly
import plotly.offline as offline
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
import plotly.io as pio
import shutil
from datetime import date, timedelta
from bs4 import BeautifulSoup
import csv
import numpy as np
import csv

pio.orca.config.executable = r'C:\Users\Tomasy\AppData\Local\Programs\orca\orca.exe'

app = Flask(__name__)
app.secret_key = "abcd"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

url = "http://bossa.pl/pub/metastock/mstock/mstall.zip"
url_newconnect = "http://bossa.pl/pub/newconnect/mstock/mstncn.zip"

# plotly.io.orca.config.executable = "C:\\Users\\Tomasy\\AppData\\Local\\Programs\\orca"

file_name = url.split('/')[-1]
file_name_newconnect = url_newconnect.split('/')[-1]

directory = r"D:\\dev\python biznes\\trend comparison\\files\\"
zip_file = r"D:\\dev\python biznes\\trend comparison\\"+url.split('/')[-1]
zip_file_newconnect = r"D:\\dev\python biznes\\trend comparison\\" + url_newconnect.split('/')[-1]
stock_directory = r"D:\\dev\python biznes\\trend comparison\\stockdata\\"
stock_list = os.listdir(directory)

@app.route('/' ,methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_val = request.form.get('search_box')
        if search_val:
            results = [x for x in stock_list if search_val.upper() in x[:-4]]
            return render_template('index.html', data_list=results)  
        else:
            return redirect(url_for('stock', stockval=request.form.get('stock_list_form')))
    return render_template('index.html', data_list=stock_list, show_tools=True )

@app.route('/download' ,methods=['GET', 'POST'])
def download():
     download_file()
     unzip_file()
     return "Database updated"
    
@app.route('/bookvalue',methods=['GET', 'POST'])
def bookvalue():
    return render_template('bookvalue.html', data_list=stock_list, bookvalues=price_book_value() )


@app.route('/<stockval>')
def stock(stockval):

    # pobiera dane dla waloru
    main_df = stock_data(stockval,2,120)
    # ustala ticker dla danego waloru 
    ticker = get_ticker(stockval[:-4])
    # Pobiera arkusz zleceń 
    ten_orders = order_book(ticker)
    # Pobiera wskaźniki
    indicators = company_indicators(ticker)

    # Pobiera wiadomości
    news = get_news(get_isin(stockval[:-4]))

    # Pobiera dane fiansowe
    financial_data = get_financial_data(get_isin(stockval[:-4]))
    gross_profit = []
    net_profit = []
    sales = []
    debt = []
    capital = []
    dates = [x for x in financial_data[0] if x]
    try:
        for i in range(0,2):
            for val in  financial_data[1][i]:
                if len(val) > 0 :
                    if val[0] == "Zysk (strata) brutto":
                        gross_profit.append([int("".join(x.split()))*1000  for x in val[1] if x])
                    elif val[0] == "Zysk (strata) netto":
                        net_profit.append([int("".join(x.split()))*1000  for x in val[1] if x])
                    elif val[0] == "Przychody netto ze sprzedaży produktów, towarów i materiałów":
                        sales.append([int("".join(x.split()))*1000  for x in val[1] if x])
                    elif val[0] == "Zobowiązania i rezerwy na zobowiązania":
                        debt.append([int("".join(x.split()))*1000  for x in val[1] if x])
                    elif val[0] == "Kapitał własny":
                        capital.append([int("".join(x.split()))*1000  for x in val[1] if x])


        years = dates[4:8]
        profit_data_net_q = go.Bar(
            x=dates[0:4], 
            y=net_profit[0],
            name='net'
        )

        profit_data_gross_q = go.Bar(
            x=dates[0:4], 
            y=gross_profit[0],
            name='gross'
        )
        
        profit_layout = go.Layout(
        barmode='group'
        )

        profit_data_q = [profit_data_net_q,profit_data_gross_q ] 
        profit_fig_q = go.Figure(data=profit_data_q, layout=profit_layout)
        pio.write_image(profit_fig_q, 'static/profits_q.png',width=600, height=400)

        profit_data_net_y = go.Bar(
            x=dates[4:8], 
            y=net_profit[1],
            name='net'
        )

        profit_data_gross_y = go.Bar(
            x=years, 
            y=gross_profit[1],
            name='gross'
        )

        layout_reversed = go.Layout(
                xaxis=dict(
                    autorange='reversed'
                ),
                bargap =0.5
        )
        bars_style = go.Layout(
                bargap =0.5
        )

        profit_data_y = [profit_data_net_y, profit_data_gross_y] 
        profit_fig_y = go.Figure(data=profit_data_y, layout=layout_reversed)
        pio.write_image(profit_fig_y, 'static/profits_y.png',width=600, height=400)
        if len(sales) > 0:
            sales_status = True
            sales_q = [go.Bar(
            x=dates[0:4], 
            y=sales[0]
            )]
            fig_sales = go.Figure(data=sales_q, layout=bars_style)
            pio.write_image(fig_sales, 'static/sales_q.png',width=600, height=400)
            sales_y = [go.Bar(
            x=years, 
            y=sales[1]
            )]
            fig_sales = go.Figure(data=sales_y, layout=layout_reversed )
            pio.write_image(fig_sales, 'static/sales_y.png',width=600, height=400)
        else:
            sales_status = False
        if len(debt) > 0:
            debt_status = True
            debt_q = [go.Bar(
            x=dates[0:4], 
            y=debt[0]
            )]
            fig_sales = go.Figure(data=debt_q, layout=bars_style)
            pio.write_image(fig_sales, 'static/debt_q.png',width=600, height=400)
            debt_y = [go.Bar(
            x=years, 
            y=debt[1]
            )]
            fig_sales = go.Figure(data=debt_y, layout=layout_reversed)
            pio.write_image(fig_sales, 'static/debt_y.png',width=600, height=400)
        else:
            debt_status = False

        if len(capital) > 0:
            capital_status = True
            capital_q = [go.Bar(
            x=dates[0:4], 
            y=capital[0]
            )]
            fig_sales = go.Figure(data=capital_q, layout=bars_style)
            pio.write_image(fig_sales, 'static/capital_q.png',width=600, height=400)
            capital_y = [go.Bar(
            x=years, 
            y=capital[1]
            )]
            fig_sales = go.Figure(data=capital_y, layout=layout_reversed)
            pio.write_image(fig_sales, 'static/capital_y.png',width=600, height=400)
        else:
            capital_status = False

    except:
            sales_status = False
            debt_status = False
            capital_status = False
            print("no financial")


    # Pobiera dane o akcjonariacie
    shareholders = get_shareholders(ticker)

    # Pobiera opis firmy
    company_details = company_info(ticker)
    
    # Pobiera szczegółowe dane o transakcjach
    transaction_data(stockval)

    # Zwraca volumen akcji, który został nabyty po danej cenie. 
    stock_prices = analyze_stock_transactions(stockval)
    vol_x , vol_y = zip(*stock_prices)

    vol_data = [go.Bar(
            x=vol_y,
            y=vol_x,
            orientation = 'h'
    )]

    vol_layout = go.Layout(
    yaxis=dict(
        dtick=0.25,
    )
)
    vol_fig = go.Figure(data=vol_data, layout = vol_layout)
    pio.write_image(vol_fig, 'static/daily_volume.png',width=700, height=500)
    

    sma_100 = sma(stockval, 100)
    sma_200 = sma(stockval, 200)

    a = daily_return(stockval)
    data = [
    go.Bar(
        x=a.index, 
        y=a['<CLOSE>']
    )
    ]
    fig = go.Figure(data=data)
    pio.write_image(fig, 'static/daily_return.png',width=600, height=400)

    # Histogram dziennych zwrotów
    histogram = [go.Histogram(x=a['<CLOSE>'])]
    hist_layout = go.Layout(xaxis=dict(
        tick0=0,
        dtick=2.0,
    ),bargap=0.1)
    histogram_fig = go.Figure(data=histogram, layout=hist_layout)
    pio.write_image(histogram_fig, 'static/histogram.png', width=550, height=350)
    
    # Średnie kroczące
    sma100 = go.Scatter(
    x = sma_100.index,
    y = sma_100['<CLOSE>'],
    line = dict(color = '#af211c',
    dash = 'dot'),
    opacity = 0.8,
    name = 'sma 100'
    )

    sma200 = go.Scatter(
    x = sma_200.index,
    y = sma_200['<CLOSE>'],
    line = dict(color = '#bc59ff',
    dash = 'dot'),
    opacity = 0.8,
    name = 'sma 200'
    )

    #  Bollinger bands + wykres świecowy
    boll = bollinger(stockval)

    boll_high = go.Scatter(
    x=boll[0].index,
    y=boll[0]['<CLOSE>'],
    line = dict(color = '#17BECF'),
    opacity = 0.8,
    name = 'bollinger up')

    boll_min = go.Scatter(
    x=boll[1].index,
    y=boll[1]['<CLOSE>'],
    line = dict(color = '#17BECF'),
    opacity = 0.8,
    name = 'bollinger 65 mean')

    boll_low = go.Scatter(
    x=boll[2].index,
    y=boll[2]['<CLOSE>'],
    line = dict(color = '#17BECF'),
    opacity = 0.8,
    name = 'bollinger down')

    vol = go.Bar(
    x=main_df[-90:].index,
    y= main_df[-90:]['<VOL>'],
    marker=dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=0.5),
            ),
    opacity = 0.2,
    yaxis='y2',
    name = 'volume')

    candle_boll = go.Candlestick(
    x = main_df[:90].index, open = main_df[:90]['<OPEN>'], high = main_df[:90]['<HIGH>'], low = main_df[:90]['<LOW>'], close = main_df[:90]['<CLOSE>'])
    candle_layout = go.Layout(
        xaxis = dict(rangeslider = dict(visible= False)),
        yaxis2=dict(
        title='Volume',
        overlaying='y',
        side='right'
    ))

    boll_data = [boll_high,boll_min,boll_low,candle_boll,vol,sma100,sma200]

    boll_fig = dict(data=boll_data, layout=candle_layout)

    pio.write_image(boll_fig, 'static/chart.png', width=1920, height=1080)


    return render_template('stock.html', data_list=stock_list, stock_name=stockval[:-4], o_book=ten_orders, close_value = main_df.iloc[-1]['<CLOSE>']
    , daily_return = round(a.iloc[-1]['<CLOSE>'],2), indicators=indicators, stock_news=news, shareholder = shareholders, ticker=ticker, fin_data = financial_data,
    prices = stock_prices, details = company_details, sales_status=sales_status, debt_status=debt_status, capital_status=capital_status) 

@app.route('/calendar',methods=['GET', 'POST'])
def calendar():
    return render_template('calendar.html',data_list=stock_list, calendar_data = get_calendar() )


@app.route('/analyze',methods=['GET', 'POST'])
def data_analyze():
    if request.method == 'POST':
        # temp_list = []
        res = []
        for val in stock_list:
            ticker = get_ticker(val[:-4])
            df = stock_data(val,2,90)
            # średni wolumen
            vol_mean = df[['<VOL>']].mean() 
            # minimalny wolumen
            min_vol = 40000
            # wartość wolumenu
            try:
                # wartość ostatniego wolumenu 
                curr_vol = df.iloc[-1]['<CLOSE>'] * df.iloc[-1]['<VOL>']
                percent_diff = ((df.iloc[-1]['<VOL>'] / vol_mean['<VOL>']) - 1 )*100
                if (curr_vol > min_vol) :
                    change = daily_return(val)
                    print(val, curr_vol)
                    res.append([val,ticker, df.iloc[-1]['<VOL>'],vol_mean['<VOL>'].round(0), round(percent_diff,2),round(change.iloc[-1]['<CLOSE>'],2) ])
                else:
                    print('za mały obrót')    
            except:
                # temp_list.append(val)
                print('Brak wartości w polu') 
        res.sort(key = lambda x : x[4], reverse=True)
        # with open('oldstocks.csv','w') as write:
        #     writer = csv.writer(write,delimiter="\n")
        #     writer.writerow(temp_list)
        return render_template('analyze.html',data_list=stock_list, results=res)
    return render_template('index.html')


@app.route('/indecies/<val>',methods=['GET', 'POST'])
def indecies(val):
    index_komp = []
    wig_20_val = []
    if request.method == 'POST':
        # wig_data = request.form['id']
        file_name = val + '.csv'
        with open(file_name, newline='') as komp_csv_file:
            wig_reader = csv.DictReader(komp_csv_file, delimiter=',')
            for val in wig_reader:
                index_komp.append(val['Ticker'])
        with open('stock_tickers_nowy.csv', newline='') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')
            for row in reader:
                if row['ticker'] in index_komp:
                    f_name = row['nazwa']+'.mst'
                    d_return = daily_return(f_name)
                    main_df = stock_data(f_name,2,120)
                    wig_20_val.append([f_name,row['ticker'],round(d_return.iloc[-1]['<CLOSE>'],2),main_df.iloc[-1]['<CLOSE>']] )
        return render_template('indecies.html',data_list=stock_list, results=wig_20_val)
    if request.method == 'GET':
        return render_template('indecies.html',data_list=stock_list, results=wig_20_val)


@app.route('/marketdata',methods=['GET', 'POST'])
def market_data():
    data = download_marketdata()
    short_sale_data = short_sale()
    return render_template('marketdata.html',data_list=stock_list, data=data, short_sale= short_sale_data)
# Pobiera dane z bossa.pl wypakowuje i usuwa plik zip z systemu
def download_file():
    try:
        print('Downloading GPW...')
        r = requests.get(url)
        with open (file_name, "wb") as code:
            code.write(r.content)
        print('Downloading GPW finished')

        print('Downloading New Connect...')
        r_n = requests.get(url_newconnect)
        with open (file_name_newconnect, "wb") as code_newconnect:
            code_newconnect.write(r_n.content)
        print('Downloading New Connect finished')
    except:
        print("something went wrong :( with downloading")

# Wypakowuje dane z pliku zip      
def unzip_file():
    try:
        print('Unzipping GPW file...')
        with zipfile.ZipFile(file_name) as myzip:
            myzip.extractall(directory)
        print('GPW files unziped')
        if os.path.isfile(zip_file):
            os.remove(zip_file) 
        print('Unzipping Newconnect file...')
        with zipfile.ZipFile(file_name_newconnect) as myzip_newconnect:
            myzip_newconnect.extractall(directory)
        print('Newconnect files unziped')
        if os.path.isfile(zip_file_newconnect):
            os.remove(zip_file_newconnect) 
        # Usuwa pliki ze starymi akcjami  
        print('Start to delete old files')
        with open('oldstocks.csv', newline='') as file:
            reader = csv.reader(file, delimiter=' ')
            for item in list(reader)[:-1]:
                file_path = r"D:\\dev\\python biznes\\trend comparison\\files\\"+item[0]
                if os.path.isfile(file_path):
                    os.remove(file_path)
        print('Old files deleted')
        print('Deleting other files')
        current_stocks = csv.DictReader(open('stock_tickers_nowy.csv'), delimiter=';')
        ticker_list = []
        for v in current_stocks:
            ticker_list.append(v['ticker'])
        for file in os.listdir(directory):
            if get_ticker(file[:-4]) not in ticker_list:
                other_files= r"D:\\dev\\python biznes\\trend comparison\\files\\"+file
                if os.path.isfile(other_files):
                    os.remove(other_files)
        print('Other files deleted')
    except:
        print("something went wrong :( with unzipping file")

# Pobiera dziesięć zleceń kupna i sprzedaży na podstawie tickera danych akcji 
def order_book(ticker):
    base_url = r'https://gragieldowa.pl/spolka_arkusz_zl/spolka/'
    if ticker:
        page = requests.get(base_url+ticker)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find_all('tr')
            headers = []
            buy = []
            sell = []
            for i in range(4,len(table)-29):
                if table[i].find('th'):
                    headers.append(i)
            if headers:
                for val_buy in range(headers[0]+1,headers[1]):
                    buy_row_member = []
                    buy_row_member.append(table[val_buy].find('td').string)
                    sibling = (table[val_buy].find('td').next_siblings)
                    for s in sibling:
                        buy_row_member.append(s.string)
                    buy.append(buy_row_member)
                for val_sell in range(headers[1]+1,len(table)-29):
                    sell_row_member = []
                    sell_row_member.append(table[val_sell].find('td').string)
                    sibling = (table[val_sell].find('td').next_siblings)
                    for s in sibling:
                        sell_row_member.append(s.string)
                    sell.append(sell_row_member)  
                if len(buy) < 11:
                    buy = buy[:len(buy)-1]
                else:
                    buy = buy[0:10]
                if len(sell) < 11:
                    sell = sell[:len(sell)-1]
                else:
                    sell = sell[0:10]
                return (buy, sell)
            else:
                return ([0], [0])
        else:
            print('something went wrong with book order scrapping')

# Na podstawie nazwy spółki zwraca jej ticker
def get_ticker(stock_name):
    stock_n = stock_name.upper()
    with open('stock_tickers_nowy.csv', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')
        for row in reader:
            if row['nazwa'] == stock_n:
                return (row['ticker'])


# Pobiera ISIN
def get_isin(stock_name):
    stock_n = stock_name.upper()
    with open('stock_tickers_nowy.csv', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')
        for row in reader:
            if row['nazwa'] == stock_n:
                return (row['ISIN'])
                

# Zwraca kursu danego waloru 
# opcja 1 bez wolumenu 
# opcja 2 z wolumenem 

def stock_data(stockval,option,days):
    start_date = date.today() - timedelta(days = days)
    end_date = date.today()
    dates = pd.date_range(start_date,end_date)
    main_df = pd.DataFrame(index=dates)
    df_wig20 = pd.read_csv(r'D:\\dev\python biznes\\trend comparison\\files\\WIG20.mst', index_col='<DTYYYYMMDD>', parse_dates=True, usecols=['<DTYYYYMMDD>','<CLOSE>'], na_values=['nan'])
    df_wig20 = df_wig20.rename(columns={'<CLOSE>':'WIG20'})
    main_df = main_df.join(df_wig20)
    main_df = main_df.dropna()
    file_path = r'D:\\dev\python biznes\\trend comparison\\files\\{}'.format(stockval)
    if os.path.isfile(file_path):
        df_temp = pd.read_csv(file_path , index_col='<DTYYYYMMDD>', parse_dates=True, usecols=['<DTYYYYMMDD>','<OPEN>','<HIGH>','<LOW>','<CLOSE>','<VOL>'], na_values=['nan'],encoding = "ISO-8859-1")
        main_df = main_df.join(df_temp)
        main_df = main_df.dropna()
        if option == 1:
            main_df = main_df.iloc[:,1:5]
        if option == 2:
            main_df = main_df.iloc[:,1:6]
        return main_df

# Dzienny zwrot z danego waloru
def daily_return(stockval):
    stock_values = stock_data(stockval,1,90)
    sv_min = stock_values[['<CLOSE>']].shift()
    res = (stock_values.divide(sv_min)-1)*100
    res.iloc[0,:] = 0
    return res[['<CLOSE>']]

# Bollinger bands 
def bollinger(stockval):
    data =  stock_data(stockval,1,365)
    nr_elements = len(data.index)
    if nr_elements > 65:
        std_deviation = data[['<CLOSE>']].rolling(65).std()
        std_deviation = std_deviation.dropna()
        mean = data[['<CLOSE>']].rolling(65).mean()
        mean = mean.dropna()
        mean_up = mean + 2*std_deviation
        mean_down = mean - 2*std_deviation
        boll_data = (mean_up.iloc[-90:], mean.iloc[-90:], mean_down.iloc[-90:])
        return boll_data

# Pobiera dane o wskaźnikach ze stooq
def company_indicators(stock_ticker):
    base_url = r'https://stooq.pl/q/g/?s='
    if stock_ticker:
        page = requests.get(base_url+stock_ticker)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find_all('tr', id='f13')
            company_data = []
            for tab in table:
                td = tab.find_all('td')
                temp = []
                for i in td:
                    temp.append(i.getText())
                company_data.append(temp)
            cz = soup.find_all('table', id='t1')
            cwk_val = cz[1].find_all('td', id='f13')
            cz_val = cz[0].find_all('td', id='f13')
            if cwk_val:
                company_data.append(['C/WK',cwk_val[-1].getText()])
            else:
                company_data.append(['C/WK','N.A'])
            if cz_val:
                company_data.append(['C/Z',cz_val[0].getText()])
            else:
                company_data.append(['C/Z','N.A'])
            return company_data

# Oblicza średnią kroczącą
def sma(stockval, value):
    data =  stock_data(stockval,1,365)
    mean = data[['<CLOSE>']].rolling(value).mean()
    mean = mean.dropna()
    nr_elements = len(data.index)
    if nr_elements > 65:
        return mean.iloc[-65:]
    else:
        return mean

# Pobiera komunikaty o danej spółce
def get_news(isin):
    base_url = r'https://www.money.pl/gielda/spolki-gpw/'
    if isin:
        page = requests.get(base_url+isin+',emitent,1.html')
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find_all('tr', {"class":'npeb8d-3'})
            news = []
            for val in table:
                td = val.find_all('td')
                data = []
                for v in td:
                    data.append(v.getText())
                    if v.find('a'):
                        link = r'https://www.money.pl' + v.find('a')['href']
                        data.append(link)
                news.append(data)
            return news[1:10:]

# Pobiera dane o akcjonariacie
def get_shareholders(stock_ticker):
    base_url = r'https://stooq.pl/q/h/?s='
    if stock_ticker:
        page = requests.get(base_url+stock_ticker)
        rows_data = []
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find_all('table',class_="fth1")
            rows = table[0].find_all('tr',id='r')
            for v in rows:
                row_values = []
                for item in v.findChildren('td'):
                    row_values.append(item.getText())
                rows_data.append(row_values)
        return rows_data

# Pobiera dane o finansach danej społki
def get_financial_data(isin):
    base_url = r'https://www.money.pl/gielda/spolki-gpw/'
    if isin:
        page = requests.get(base_url+isin+',finanse.html')
        if page.status_code == 200:
            soup = BeautifulSoup(page.content , 'html.parser',from_encoding="utf-8")
            table = soup.find_all(class_='fkmtpn-1')
            financial_years = []
            financial_data = []
            for item in table:
                data_table = item.find_all('tr', {"class":'fkmtpn-2'})
                all_data_table = []
                for val in data_table:
                    financial_data_item = []
                    td_head = val.find('td', {"class":'fkmtpn-5'})
                    td_values = val.find_all('td',{"class":'fkmtpn-6'})
                    td_years = val.find_all('td',{"class":'fkmtpn-4'})
                    for year in td_years:
                        financial_years.append(year.getText())
                    if td_head:
                        financial_data_item.append(td_head.getText())
                        if td_values:
                            temp_val = []
                            for item in td_values:
                                text = item.getText()
                                temp_val.append(text.replace(u'\xa0', ' '))
                            financial_data_item.append(temp_val)
                    all_data_table.append(financial_data_item)
                financial_data.append(all_data_table)
            return financial_years, financial_data
            
# Pobiera dane o tranzakcjach na danym walorze 
def transaction_data(stockval):
    url = r'http://bossa.pl/pub/intraday/mstock/cgl/'
    file_name = stockval[:-4] + '.zip'
    full_url = url + file_name
    zip_stock_file = r"D:\\dev\python biznes\\trend comparison\\"+file_name
    try:
        print("Downloading" + stockval[:-4] + '.zip')
        r = requests.get(full_url)
        with open(file_name , "wb") as code:
            code.write(r.content)
        print("Downloading " + stockval[:-4] + '.zip' + " finished")
        try:
            if os.path.isdir(stock_directory):
                shutil.rmtree(stock_directory)
                os.mkdir(stock_directory)
            else:
                os.mkdir(stock_directory)
            with zipfile.ZipFile(file_name) as file_to_unzip:
                file_to_unzip.extractall(stock_directory)
            if os.path.isfile(zip_stock_file):
                os.remove(zip_stock_file)
        except:
            print("Something went wrong :( with uzipping stock zip")
    except:
        print("Something went wrong :( with downloading stock file")


def analyze_stock_transactions(stockval):
    stock = stock_directory + stockval[:-4] + '.prn'
    df = pd.read_csv(stock)
    df.columns = ["ticker","zero","date","time","open","high","low","close","volume","nextzero"]
    last_day =  df.loc[df["date"] == df.iloc[-1]["date"]]
    stock_values = last_day["close"].values
    stock_volume = last_day["volume"].values
    transactions_stats = {}
    results = []
    for i in range(len(stock_values)):
        if transactions_stats.get(stock_values[i]):
            transactions_stats[stock_values[i]] = transactions_stats[stock_values[i]] + stock_volume[i]
        else:
            transactions_stats[stock_values[i]] = stock_volume[i]
    for key, val in transactions_stats.items():
        temp = [key,val]
        results.append(temp)
    results = sorted(results, key= lambda x : x[1], reverse= True)
    return results
        

def download_marketdata():
    base_url = r'https://stooq.pl/t/bt/'
    page = requests.get(base_url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find_all('tbody', id='r')
        rows = table[0].find_all('tr')
        data = []
        for row in rows:
            elements = row.find_all('td')
            table_row = []
            for item in elements:
               table_row.append(item.getText())
            data.append(table_row)
        return data

def short_sale():
    base_url = r'https://rss.knf.gov.pl/RssOuterView/faces/hspsList.xhtml'
    page = requests.get(base_url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find_all('tbody')
        rows = table[0].find_all('tr')
        short_sale_data = []
        for val in rows:
            temp = val.find_all('td')
            temp_val = []
            for data in temp:
                temp_val.append(data.getText())
            short_sale_data.append(temp_val)
        return short_sale_data

def company_info(stock_ticker):
    base_url = r'https://stooq.pl/q/p/?s='
    if stock_ticker:
        page = requests.get(base_url+stock_ticker)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            full_company_name = soup.find('font', id='f14')
            table = soup.find('font', id='f13')
            company_details = []
            company_details.append(full_company_name.getText())
            table_converted =list(table)
            company_details.append(table_converted[0])
            company_details.append(table_converted[2])
            company_details.append(table_converted[4])
            company_details.append(table_converted[6])
            for i in enumerate(table_converted[9]):
                company_details.append(i[1])
            for j in enumerate(table_converted[12]):
                company_details.append(j[1])
            company_details.append(table_converted[21])
            return company_details

def price_book_value():
    data = {}
    results = []
    for item in stock_list:
        try:
            data[get_ticker(item[:-4])] = company_indicators(get_ticker(item[:-4]))
            val = company_indicators(get_ticker(item[:-4]))
            if val[14][0] == 'C/WK' and val[14][1] != 'N.A':
                print([item[:-4],get_ticker(item[:-4]) ,float(val[14][1])])
                results.append([item[:-4],get_ticker(item[:-4]) ,float(val[14][1])])
        except:
            print("Problem with {}".format(item))
    results.sort(key = lambda x: x[2])
    return results
    
# Pobiera kalendarz wydarzeń giełdowych
def get_calendar():
    base_url = r'https://www.bankier.pl/gielda/kalendarium/'
    page = requests.get(base_url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find('div', {"id": "calendarContent"})
        days = table.find_all('div',{"class":"calendarDay"})
        calendar_data = []
        for day in days:
            day_date = day.find("time").text.strip().replace(u'\xa0', ' ')
            events = day.find_all('div', {"class":"event"})
            date_events = []
            for event in events:
                calendar_data.append([day_date, event.find('div', {"class": "company"}).text.strip(), event.find('div', {"class":"eventDescription"}).text.strip()])
        print(calendar_data)
        return calendar_data