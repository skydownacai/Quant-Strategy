default_setting = '''backtest
start: 2019-06-10 00:00:00
end: 2019-08-10 00:00:00
period: 1m
exchanges: [{"eid":"Bitfinex","currency":"BTC_USD","balance":10000,"stocks":3}]'''
from fmz import *
import pandas as pd
from matplotlib.pylab import date2num ## 导入日期到数值一一对应的转换工具
import json
from  datetime import datetime,timedelta
import matplotlib.pyplot as plt
import matplotlib
import random
from hmmlearn import hmm
from dateutil.parser import parse ## 导入转换到指定格式日期的工具
import numpy as np
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family']='sans-serif'
#解决负号'-'显示为方块的问题
matplotlib.rcParams['axes.unicode_minus'] = False
import mpl_finance as mpf

class PeriodTooLess(Exception):
    def __init__(self):
        pass
def TIME_STAMP(TIME,mode = 1):
    '返回字符串时间戳'
    if mode:
        return int(time.mktime(time.strptime(TIME+' 08:00:00','%Y-%m-%d %H:%M:%S')))
    else:
        return int(time.mktime(time.strptime(TIME,'%Y-%m-%d %H:%M:%S')))
ALL_month = [
]
ALL_day = []
startday = datetime.strptime('2018-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
endday   = datetime.strptime('2019-08-10 00:00:00', '%Y-%m-%d %H:%M:%S')
while True:
    ALL_day.append(str(startday))
    if str(startday) == str(endday):
        break
    lastday = startday - timedelta(days=1)
    if lastday.month != startday.month:
        ALL_month.append(str(startday))
    startday = startday + timedelta(days=1)
class settings:
    def __init__(self,start = "2019-06-10 00:00:00",end="2019-07-10 00:00:00",eid = "Bitfinex",currency ="BTC_USD",balance = "10000",stocks = "1",period = "1d"):
        self.setting_str = default_setting
        self.settings = {
            "start":start,
            "end"  :end,
            "eid"  :eid,
            "currency":currency,
            "balance":str(balance),
            "stocks":str(stocks),
            "period":period
        }
        self.setting_str = self.setting_str.replace("2019-06-10 00:00:00",self.settings["start"])
        self.setting_str = self.setting_str.replace("2019-08-10 00:00:00",self.settings["end"])
        self.setting_str = self.setting_str.replace("Bitfinex",self.settings["eid"])
        self.setting_str = self.setting_str.replace("BTC_USD",self.settings["currency"])
        self.setting_str = self.setting_str.replace("10000",self.settings["balance"])
        self.setting_str = self.setting_str.replace("stocks:3","stocks:{}".format(float(self.settings["stocks"])))
        self.setting_str = self.setting_str.replace("1m",self.settings["period"])
    def export(self):
        return self.setting_str
def get_day(timestamp):
    '返回月份 与 日'
    format_time = time.localtime(timestamp/1000)
    return (format_time[0],format_time[1],format_time[2])
class strategy:
    def __init__(self):
        pass
    def init(self,PRINT = False):
        self.task = VCtx(self.setting)
        self.init_account = exchange.GetAccount()
        self.realizible_profit = 0
        if PRINT:
            print("Strategy Name:",self.name)
            print("Setting:", self.setting)
        #print(self.setting)
        #print("初始账户信息:",self.init_account)
    def main(self):
        while True:
            self.onTick()
            Sleep(1000)
    def exit_f(self):
        pass
    def format_outcome(self):
        for key in self.outcome:
            if key == "RuntimeLogs":
                continue
            if type(self.outcome[key]) != type([]) and type(self.outcome[key]) != type({}):
                print(key, self.outcome[key])
            elif type(self.outcome[key]) == type({}):
                print(key)
                for small_key in self.outcome[key]:
                    print('   ', small_key, self.outcome[key][small_key])
            else:
                print(key)
                for item in self.outcome[key]:
                    for small_key in item:
                        print('   ', small_key, item[small_key])
        #for Log in self.outcome['RuntimeLogs']:
            #print(Log)
    def run(self,PRINT = False):
        '''运行回测然后得到收益'''
        self.init(PRINT)
        try:
            self.main()
        except EOFError:
            #print("回测结束\n")
            self.exit_f()
            self.outcome = json.loads(self.task.Join())
            for Log in self.outcome['RuntimeLogs']:
                Log[1] = get_day(Log[1])
                #print(Log)
            Snapshort = self.outcome['Snapshort'][0]
            balance_change = Snapshort['Balance'] - self.init_account['Balance']
            stock_change = Snapshort['Stocks'] - self.init_account['Stocks']
            self.realizible_profit = balance_change + stock_change * Snapshort['Symbols']['BTC_USD_Bitfinex']['Last'] - Snapshort['Commission']
            self.commission = float(Snapshort['Commission'])
            #print(Snapshort)
    def Multiperiodbacktest(self,periods,filename = time.strftime("%b_%d_%Y_%H_%M_%S", time.localtime(time.time()))):
        result = {
            "period":[],
            "profit":[],
            "commission":[],
        }

        if len(periods) <= 1:
            raise PeriodTooLess
        labels = []
        this_dir = self.dir +filename + "/"
        try:
            os.mkdir(this_dir)
        except:
            pass
        write = pd.ExcelWriter(this_dir+ "result.xls")
        for period in periods:
            start = period[0]
            end = period[1]
            if start.endswith("00:00:00"):
                start  = start[:10]
            if end.endswith("00:00:00"):
                end    = end[:10]
            key = start
            labels.append(start)
            print('period:',start + " - " + end)
            result['period'].append(start + " - " + end)
            self.backtest(start,end,False,False)
            result['profit'].append(self.realizible_profit)
            result['commission'].append(self.commission)
        pd.DataFrame(result).to_excel(write,sheet_name="具体收益")
        average_profit = sum(result['profit'])/len(result['profit'])
        samplenum = len(result['profit'])
        inflowmonthnum = sum([1 if profit > 0 else 0 for profit in result['profit']])
        metrics = {
            "average_profit":[average_profit],
            "极差":[max(result['profit']) - min(result['profit'])],
            "正收益月数":[inflowmonthnum],
            "正收益月数比率":[round(inflowmonthnum/samplenum,2)],
            "平均手续费":[round(sum(result['commission'])/samplenum,2)],
            "参数:":[" "]
        }
        for key in self.param:
            metrics[key] = [self.param[key]]
        pd.DataFrame(metrics).to_excel(write, sheet_name="指标")
        write.save()
        fig = plt.figure(figsize=(20,8),frameon =False)
        ax = plt.gca()
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        plt.plot()
        plt.plot(list(range(samplenum)),result['profit'],label = 'profit')
        plt.plot(list(range(samplenum)),[average_profit]*samplenum,label = "average = {}".format(average_profit))
        plt.legend(loc = 'upper right')
        plt.xlabel("period")
        plt.ylabel("profit")
        plt.xticks(list(range(samplenum)),labels,rotation = 45)
        plt.title("profit curve")
        plt.savefig(this_dir + "profitcurve.png")
        print("done!:",filename)
        return result
    def dailybacktest(self,gap):
        period = []
        for i in range(len(ALL_day) - gap):
            period.append((ALL_day[i],ALL_day[i+gap]))
        self.Multiperiodbacktest(period,"{}日内交易回测".format(gap))
    def monthlybacktest(self,gap):
        period = []
        for i in range(len(ALL_month) - gap):
            period.append((ALL_month[i],ALL_month[i+gap]))
        suffix = ""
        for key in self.param:
            suffix += str(key) +"="+str(self.param[key]) + "&"
        self.Multiperiodbacktest(period,str(gap) + "月内交易回测(param_" + suffix[:-1]+")")
    def backtest(self,start,end,PRINTSETTING=True,PRINTLOG = False):
        #self.param["start"] = start
        #self.param['end'] = end
        if not start.endswith("00:00:00"):
            start+= " 00:00:00"
        if not end.endswith("00:00:00"):
            end  += " 00:00:00"
        self.setting = settings(start = start,end = end,period='1d').export()

        self.run(PRINT=PRINTSETTING)
        print('profit', self.realizible_profit)
        if PRINTLOG:
           for log in  self.outcome['RuntimeLogs'][::-1]:
                print(log)
    @property
    def param_suffix_str(self):
        suffix = ""
        for key in self.param:
            suffix += str(key) +"="+str(self.param[key]) + "&"
        suffix = suffix[:-1]
        return suffix
    @ property
    def setting(self):
        try:
            return self._setting
        except AttributeError:
            self._setting = settings().export()
            return self._setting
    @ setting.setter
    def setting(self,value):
        self._setting = value
    @property
    def param(self):
        try:
            return self._param
        except AttributeError:
            self._param = {}
            return self._param
    @param.setter
    def param(self,value):
        self._param = value
    def __getitem__(self, item):
        return self._param[item]
    def __setitem__(self, key, value):
        self._param[key] = value
    @property
    def name(self):
        if self._name not in locals().keys():
            self._name =  "Unnamed Strategy"
        return self._name
    @name.setter
    def name(self,value):
        self._name = value
        self.dir = self._name + "/"
        if os.path.exists(self.dir) == False:
            os.mkdir(self.dir)
    @staticmethod
    def ticktime(tick):
        return (time.strftime("%b %d %Y %H:%M:%S", time.localtime(int(str(tick['Time'])[:-3]))))
class R_breaker(strategy):
    '''
    p : 每次日内交易的btc个数
    '''
    def load_param(self,p = 0.1):
        self
        self.p = p
    def main(self):
        LastDay = get_day(exchange.GetRecords(PERIOD_D1)[-1].Time - 1000)
        LastTimeStamp = exchange.GetRecords(PERIOD_D1)[-1].Time / 1000
        yestoday = 0
        BreakSsteup = False
        BreakBsteup = False
        STATE = "IDLE"
        Fan = False
        while True:
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                STATE = "IDLE"
                yestoday = exchange.GetRecords(PERIOD_D1)[-2]  # -1是今日
                BreakSsteup = False
                BreakBsteup = False
                Log(NowDay)
                Fan = False
            NowPrice = ticker.Last
            High = yestoday.High
            Low = yestoday.Low
            Close = yestoday.Close
            Open = yestoday.Open
            TodayHigh = ticker.High
            TodayLow = ticker.Low
            Ssteup = High + 0.35 * (Close - Low)  # 观察卖出价
            Bsteup = Low - 0.35 * (High - Close)  # 观察买入价
            Senter = 1.07 / 2 * (High + Low) - 0.07 * Low  # 反转卖出价
            Benter = 1.07 / 2 * (High + Low) - 0.07 * High  # 反转买入价
            Bbreak = Ssteup + 0.25 * (Ssteup - Bsteup)  # 突破买入价
            Sbreak = Bsteup - 0.25 * (Ssteup - Bsteup)  # 突破卖出价
            if TodayHigh > Ssteup:
                BreakSsteup = True
            if TodayLow < Bsteup:
                BreakBsteup = True
            '''
            空仓的情况下:趋势跟踪
              1.如果盘中价格超过突破买入价，则采取趋势策略，即在该点位开仓做多
              2.如果盘中价格跌破突破卖出价，则采取趋势策略，即在该点位开仓做空
            持仓的情况下:
              1.当日内最高价超过观察卖出价后，盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，采取反转策略，即在该点位（反手、开仓）做空；
              2.当日内最低价低于观察买入价后，盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，采取反转策略，即在该点位（反手、开仓）做多；
            '''
            if STATE == "IDLE":
                if NowPrice > Bbreak:
                    Log("价格超过突破买入价，趋势跟踪开仓做多")
                    exchange.Buy(ticker.Sell * 1.001, self.p)
                    STATE = "LONG"
                elif NowPrice < Sbreak:
                    Log("价格跌破突破卖出价，趋势跟踪开仓做空")
                    exchange.Sell(ticker.Buy * 0.999, self.p)
                    STATE = "SHORT"
            else:
                if BreakSsteup and NowPrice < Senter and STATE == "LONG" and Fan == False:
                    Log("当日内最高价超过观察卖出价，盘中价格回落跌破反转卖出价,反手做空")
                    exchange.Sell(ticker.Buy * 0.999, 2 * self.p)
                    STATE = "SHORT"
                    Fan = True
                if BreakBsteup and NowPrice > Benter and STATE == "SHORT"and Fan == False:
                    Log("当日内最低价低于观察买入价，盘中价格回落跌破反转卖出价,反手做多")
                    exchange.Buy(ticker.Sell * 1.001, 2 * self.p)
                    STATE = "LONG"
                    Fan = True
            '''每日收盘前2分钟,进行平仓'''
            if ticker.Time / 1000 - LastTimeStamp >= 86250:
                LastTimeStamp = LastTimeStamp + 86400
                if STATE == "LONG":
                    Log("每日收盘平仓")
                    exchange.Sell(ticker.Buy * 0.999, self.p)  # 做多后做空平仓
                if STATE == "SHORT":
                    Log("每日收盘平仓")
                    exchange.Buy(ticker.Sell * 1.001, self.p)  # 做空后做多平仓
                Log(exchange.GetAccount())
            LastDay = NowDay
            Sleep(500)
class Dual_Thrust(strategy):
    def __init__(self):
        self.name = 'DualThrust'
        self.param = {
            "N":5,
            "k1":0.9,
            "k2":0.5,
            "p":1
        }
    def main(self):
        Histroy_record = exchange.GetRecords()
        dopen = Histroy_record[-1].Open  # 每日的开盘价
        LastDay = get_day(Histroy_record[-1].Time / 1000)  # 上一次获取行情的日期
        Nperiod = Histroy_record[-1 * self.param['N'] - 1:][:-1]  # 前N日的K数据
        Track = self.get_track(Nperiod,dopen)  # 获取上下轨数据
        LastState = 'IDLE'
        while True:
            ticker = exchange.GetTicker()
            #print(time.strftime("%b %d %Y %H:%M:%S",time.localtime(int(str(ticker['Time'])[:-3]))))
            NowPrice = ticker.Last  # 当前市场最后成交价格
            NowDay = get_day(ticker.Time)  # 当前日期
            if (NowDay != LastDay):
                # 进入了新的一天，重新更新前N天数据与今日开盘价,与今日上下轨点数
                Histroy_record = exchange.GetRecords(PERIOD_D1)

                #for tick in Histroy_record:
                #    print(time.strftime("%b %d %Y %H:%M:%S",time.localtime(int(str(tick['Time'])[:-3]))))
                Nperiod = Histroy_record[-1 * self.param['N'] - 1:][:-1]
                dopen = Histroy_record[-1].Open
                Track = self.get_track(Nperiod,dopen)
                Log(NowDay, ':', Log(exchange.GetAccount()))
            if (NowPrice > Track['uptrack'] and LastState != 'LONG'):
                Log('当前市价格', NowPrice, '突破做多触发价:', Track['downtrack'])
                # cancel_pending_orders(ORDER_TYPE_SELL) # 撤回所有卖单
                if LastState == "IDLE":
                    exchange.Buy(ticker.Sell * 1.001, self.param['p'])
                else:
                    exchange.Buy(ticker.Sell * 1.001, 2 * self.param['p'])
                    # days_operation = True
                LastState = 'LONG'
            if (NowPrice < Track['downtrack'] and LastState != 'SHORT'):
                Log('当前市价格', NowPrice, '突破做空触发价:', Track['downtrack'])
                # cancel_pending_orders(ORDER_TYPE_BUY) # 撤回所有买单
                if LastState == "IDLE":
                    exchange.Sell(ticker.Buy * 0.999, self.param['p'])
                else:
                    exchange.Sell(ticker.Buy * 0.999, 2 * self.param['p'])
                LastState = 'SHORT'
            LastDay = NowDay  # 更新上次获取行情的日期
    def get_track(self,Nperiod,dopen):
        '获得上下轨点数'
        HH = max([day.High for day in Nperiod])
        LC = min([day.Close for day in Nperiod])
        HC = max([day.Close for day in Nperiod])
        LL = min([day.Low for day in Nperiod])
        RANGE = max(HH - LC, HC - LL)
        return {'uptrack': dopen + self.param['k1'] * RANGE, 'downtrack': dopen - self.param['k2'] * RANGE}
class 菲阿里四价(strategy):
    def __init__(self):
        self.name = "菲阿里四价"
        self.param['p'] = 0.1
    def main(self):
        STATE = "IDLE"
        LastDay = get_day(exchange.GetRecords(PERIOD_D1)[-1].Time)
        LastTimeStamp = exchange.GetRecords(PERIOD_D1)[-1].Time / 1000
        while True:
            p = self.param['p']
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            #TODAY = exchange.GetRecords(PERIOD_D1)[-1]
            yestoday = exchange.GetRecords(PERIOD_D1)[-2]  # -1是今日
            uptrack = yestoday.High
            downtrack = yestoday.Low
            NowPrice = ticker.Last
            if NowDay != LastDay:
                STATE = "IDLE"
                Log(NowDay)
            '''日内价格突破上下轨，进行做多或者做空'''
            if STATE == "IDLE" and NowPrice > uptrack:
                exchange.Buy(ticker.Sell * 1.001, p)
                STATE = "LONG"
            if STATE == "IDLE" and NowPrice < downtrack:
                exchange.Sell(ticker.Buy * 0.999, p)
                STATE = "SHORT"
            '''每日收盘前2分钟,进行平仓'''
            if ticker.Time / 1000 - LastTimeStamp >= 86250:
                LastTimeStamp = LastTimeStamp + 86400
                if STATE == "LONG":
                    exchange.Sell(ticker.Buy * 0.999, p)  # 做多后做空平仓
                if STATE == "SHORT":
                    exchange.Buy(ticker.Sell * 1.001, p)  # 做空后做多平仓
            LastDay = NowDay
            Sleep(500)
class skypark(strategy):
    def load_param(self,p = 0.1,k1=1.01,k2=0.99):
        self.p = p
        self.k1 = k1
        self.k2 = k2
    def main(self):
        p = self.p
        k1 = self.k1
        k2 = self.k2
        History = exchange.GetRecords(PERIOD_D1)
        TODAY = History[-1]
        Yestoday = History[-2]
        LastTimeStamp = TODAY.Time / 1000
        LastDay = get_day(TODAY.Time - 1000)
        DayFirstCandle = 0  # 每日第一个k线
        DayOpen = TODAY.Open
        LastOpen = Yestoday.Open
        STATE = "IDLE"
        while True:
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            if LastDay != NowDay:
                '进入新的更新每日第一条k线与昨日和今日的开盘价'
                DayFirstCandle = ticker
                History = exchange.GetRecords(PERIOD_D1)
                TODAY = History[-1]
                Yestoday = History[-2]
                DayOpen = TODAY.Open
                LastOpen = Yestoday.Open
                if DayOpen > LastOpen * k1:
                    Log("今日高开", "今日开盘价:", DayOpen, "昨日开盘价", LastOpen)
                if DayOpen < LastOpen * k2:
                    Log("今日低开", "今日开盘价:", DayOpen, "昨日开盘价", LastOpen)
                STATE = "IDLE"
            Nowprice = ticker.Last
            if DayOpen > LastOpen * k1 and STATE == "IDLE" and Nowprice > DayFirstCandle.High and ticker.Time / 1000 - LastTimeStamp < 86250:
                Log("价格", Nowprice, "突破上轨", DayFirstCandle.High, "，买入开仓")
                exchange.Buy(ticker.Sell * 1.001, p)
                STATE = "LONG"
            if DayOpen < LastOpen * k2 and STATE == "IDLE" and Nowprice < DayFirstCandle.Low and ticker.Time / 1000 - LastTimeStamp < 86250:
                Log("价格", Nowprice, "突破下轨", DayFirstCandle.High, "，卖入开仓")
                exchange.Sell(ticker.Buy * 0.999, p)
                STATE = "SHORT"
                '''每日收盘前2分钟,进行平仓'''
            if ticker.Time / 1000 - LastTimeStamp >= 86250:
                LastTimeStamp = LastTimeStamp + 86400
                if STATE == "LONG":
                    Log("做多后做空平仓")
                    exchange.Sell(ticker.Buy * 0.999, p)  # 做多后做空平仓
                if STATE == "SHORT":
                    Log("做空后做多平仓")
                    exchange.Buy(ticker.Sell * 1.001, p)  # 做空后做多平仓
            LastDay = NowDay  # 更新获取上一次行情的日期
class Dual_Thrust_improved(strategy):
    def __init__(self):
        self.name = 'DualThrust_improved'
        self.defaultparam = {
            "N": 5,
            "k1": 0.4,
            "k2": 0.4,
            "p": 0.1,
            'stop': 1000,
            "KDJ_N":9,
        }
        self.param = self.defaultparam.copy()
        self.k = {}
        self.d = {}
        self.j = {}

    def main(self):
        Histroy_record = exchange.GetRecords(PERIOD_D1)
        dopen = Histroy_record[-1].Open  # 每日的开盘价
        LastDay = get_day(Histroy_record[-1].Time / 1000)  # 上一次获取行情的日期
        Nperiod = Histroy_record[-1 * self.param['N'] - 1:][:-1]  # 前N日的K数据
        Track = self.get_track(Nperiod,dopen)  # 获取上下轨数据
        LastState = 'IDLE'
        self.k[LastDay] = 50
        self.d[LastDay] = 50
        self.price = 0
        while True:
            ticker = exchange.GetTicker()
            #print(time.strftime("%b %d %Y %H:%M:%S",time.localtime(int(str(ticker['Time'])[:-3]))))
            #print(ticker.Last)
            NowPrice = ticker.Last  # 当前市场最后成交价格
            NowDay = get_day(ticker.Time)  # 当前日期
            #print(time.strftime("%b %d %Y %H:%M:%S", time.localtime(int(str(ticker['Time'])[:-3]))))
            if (NowDay != LastDay):
                # 进入了新的一天，重新更新前N天数据与今日开盘价,与今日上下轨点数
                Histroy_record = exchange.GetRecords(PERIOD_D1)
                #for tick in Histroy_record:
                #    print(time.strftime("%b %d %Y %H:%M:%S", time.localtime(int(str(tick['Time'])[:-3]))))
                #exit()
                Nperiod = Histroy_record[-1 * self.param['N'] - 1:][:-1]
                dopen = Histroy_record[-1].Open
                self.KDJ(NowDay)
                if self.k[NowDay] > 50 and self.d[NowDay]  > 50 and self.j[NowDay] > 50:
                    self.param['k1'] = self.defaultparam['k1'] - 0.1
                    self.param['k2'] = self.defaultparam['k2']
                    #为做多市场，调整下轨
                if self.k[NowDay] < 50 and self.d[NowDay]  < 50 and self.j[NowDay] < 50:
                    self.param['k1'] = self.defaultparam['k1']
                    self.param['k2'] = self.defaultparam['k2'] - 0.1
                Track = self.get_track(Nperiod, dopen)
                Log(NowDay, ':', Log(exchange.GetAccount()))
            #止损
            if LastState == 'LONG' and self.price - ticker.Buy*0.999 >= self.param['stop']:
                exchange.Sell(ticker.Buy * 0.999, 1 * self.param['p'])
                LastState = "IDLE"
            if LastState == 'SHORT' and ticker.Sell*1.001 - self.price >= self.param['stop']:
                exchange.Buy(ticker.Sell *1.001, 1 * self.param['p'])
                LastState = "IDLE"
            #KDJ条件判断市场
            if (NowPrice > Track['uptrack'] and LastState != 'LONG'):
                Log('当前市价格', NowPrice, '突破做多触发价:', Track['downtrack'])
                # cancel_pending_orders(ORDER_TYPE_SELL) # 撤回所有卖单
                if LastState == "IDLE":
                    exchange.Buy(ticker.Sell * 1.001, self.param['p'])
                else:
                    exchange.Buy(ticker.Sell * 1.001, 2 * self.param['p'])
                    # days_operation = True
                self.price = ticker.Sell * 1.001
                LastState = 'LONG'
            if (NowPrice < Track['downtrack'] and LastState != 'SHORT'):
                Log('当前市价格', NowPrice, '突破做空触发价:', Track['downtrack'])
                # cancel_pending_orders(ORDER_TYPE_BUY) # 撤回所有买单
                if LastState == "IDLE":
                    exchange.Sell(ticker.Buy * 0.999, self.param['p'])
                else:
                    exchange.Sell(ticker.Buy * 0.999, 2 * self.param['p'])
                self.price = ticker.Buy * 0.999
                LastState = 'SHORT'

            LastDay = NowDay  # 更新上次获取行情的日期
    def get_track(self,Nperiod,dopen):
        '获得上下轨点数'
        HH = max([day.High for day in Nperiod])
        LC = min([day.Close for day in Nperiod])
        HC = max([day.Close for day in Nperiod])
        LL = min([day.Low for day in Nperiod])
        RANGE = max(HH - LC, HC - LL)
        return {'uptrack': dopen + self.param['k1'] * RANGE, 'downtrack': dopen - self.param['k2'] * RANGE}
    def RSV(self,Nperiod):
        Cn = Nperiod[-1].Close
        Ln = min([day.Close for day in Nperiod])
        Hn = max([day.High for day in Nperiod])
        return (Cn - Ln) / (Hn - Ln) * 100
    def KDJ(self,today):
        records = exchange.GetRecords(PERIOD_D1);
        kdj = TA.KDJ(records,self.param['KDJ_N'], 3, 3);
        #Log("k:", kdj[0], "d:", kdj[1], "j:", kdj[2]);
        self.k[today] = kdj[0][-1]
        self.d[today] = kdj[0][-1]
        self.j[today] = kdj[0][-1]
class HMM(strategy):
    def __init__(self):
        self.name = "Hiden Markov "
        self.winratio = []
        self.param = {
            "p":0.1,
            'gap':2,
            "days":200,
        }
    def testmetric(self):
        global ALL_day
        periods = []
        total_real = []
        total_metr= []
        ALL_day = ALL_day[-10:]
        for i in range(len(ALL_day)-1):
            periods.append((ALL_day[i],ALL_day[i+1]))
        labels = []
        this_dir = self.dir + self.param['metrics']+ "/"
        try:
            os.mkdir(this_dir)
        except:
            pass
        for period in periods:
            start = period[0]
            end = period[1]
            if start.endswith("00:00:00"):
                start  = start[:10]
            if end.endswith("00:00:00"):
                end    = end[:10]
            print('period:',start + " - " + end)
            self.backtest(start,end,False,False)
            labels.append(start)
            total_real += self.real
            total_metr += self.metrics
        samplenum = len(total_real)
        fig = plt.figure(figsize=(30,8))
        ax = plt.gca()
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        ax.plot(list(range(samplenum)), total_real, label='真实成交价变动')
        ax2 = ax.twinx()
        ax2.set_xlabel("sample")
        ax2.set_ylabel("number")
        # ax2.set_ylim((0,100))
        plt.title(self.param['title'])
        if self.param['metrics'] == 'MACD':
            DIF  = []
            DEA  = []
            MACD = []
            for item in total_metr:
                DIF.append(item[0])
                DEA.append(item[1])
                MACD.append(item[2])
            ax2.plot(list(range(samplenum)), DIF, color='red',
                     label="DIF")
            ax2.plot(list(range(samplenum)), DEA, color='blue',
                     label="DEA")
            ax2.plot(list(range(samplenum)), MACD, color='green',
                     label="MACD")
            ax2.legend(loc='upper right')
            plt.savefig(this_dir +self.param['title'] + ".png")
            print("done!:")
        if self.param['metrics'] == 'RSI':
            ax2.plot(list(range(samplenum)), total_metr, color='red',
                     label="该时刻前{}条1分钟k线所求出{}值".format(self.param['metrics_period'], self.param['metrics']))
            ax2.legend(loc='upper right')

            plt.savefig(this_dir + str(self.param['metrics_period'])+'_'+self.param['title'] + ".png")
            print("done!:")
        if self.param['metrics'] == 'OBV':
            ax2.plot(list(range(samplenum)), total_metr, color='red',
                     label="前一时刻所求出{}值".format(self.param['metrics']))
            ax2.legend(loc='upper right')

            plt.savefig(this_dir +self.param['title'] + ".png")
            print("done!:")
    def testall(self):
        global ALL_day
        periods = []
        total_real = []
        total_pred = []
        ratio = []
        profits = []
        ALL_day = ALL_day[-1*self.param['days']:]
        for i in range(len(ALL_day)-1):
            periods.append((ALL_day[i],ALL_day[i+1]))
        labels = []
        this_dir = self.dir + "algorithm2" + "/"
        try:
            os.mkdir(this_dir)
        except:
            pass
        if self.param['gap'] != None:
            this_dir = self.dir +"algorithm2" + "/" + str(self.param['gap']) + '/'
        else:
            this_dir = self.dir + "algorithm2" + "/"
        try:
            os.mkdir(this_dir)
        except:
            pass
        for period in periods:
            start = period[0]
            end = period[1]
            if start.endswith("00:00:00"):
                start  = start[:10]
            if end.endswith("00:00:00"):
                end    = end[:10]
            print('period:',start + " - " + end)
            self.backtest(start,end,False,False)
            self.predict = self.predict[:len(self.real)]
            if len(self.predict) == 0:
                print('跳过一天')
                continue
            labels.append(start)
            total_real += self.real
            total_pred += self.predict
            ratio.append(self.cal_trend_correct_ratio(self.real,self.predict))
            profits.append(self.realizible_profit)

        sum_profit = [profits[0]]
        for i in range(1,len(profits)):
            sum_profit.append(sum_profit[-1] + profits[i])
        samplenum = len(total_real)
        fig = plt.figure(figsize=(30,5))
        above_figure, axs = plt.subplots(2,1)
        change_ax = axs[0]
        correct_ax = axs[1]

        ax = change_ax
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        ax.plot(list(range(samplenum)),total_real,label = '真实成交价变动')
        ax.plot(list(range(samplenum)),total_pred,label = "前一时刻指标值")
        ax.legend(loc = 'upper right')
        ax.set_xlabel("sample")
        ax.set_ylabel("number")
        ax.set_title("{}日内成交价真实变动与预测变动曲线".format(self.param['days']))

        ax = correct_ax
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        ax.plot(list(range(len(ratio))),ratio,label = '趋势预测正确率')
        ax.plot(list(range(len(ratio))),[np.average(ratio)]*len(ratio),label = '样本平均预测正确率')
        ax.legend(loc = 'upper right')
        ax.set_xlabel("sample")
        ax.set_ylabel("ratio")
        ax.set_title("{}日预测正确率".format(self.param['days']))
        plt.savefig(this_dir + "compare_change_and_correct_ratio_{}.png".format(self.param_suffix_str))

        fig = plt.figure()
        ax = plt.gca()
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        plt.plot(list(range(len(labels))),profits,label = '每日收益曲线')
        plt.plot(list(range(len(labels))),sum_profit,label = "累积收益曲线")
        plt.legend(loc = 'upper left')
        plt.xlabel("day")
        plt.ylabel("number")
        plt.title("{}日收益曲线".format(self.param['days']))
        plt.savefig(this_dir + "profit_curve_{}.png".format(self.param_suffix_str))
        print("done!:")
    def testprofit(self):
        global ALL_day
        periods = []
        profits = []
        labels = []
        ALL_day = ALL_day[-100:]
        for i in range(len(ALL_day)-1):
            periods.append((ALL_day[i],ALL_day[i+1]))
        for period in periods:
            start = period[0]
            end = period[1]
            if start.endswith("00:00:00"):
                start  = start[:10]
            if end.endswith("00:00:00"):
                end    = end[:10]
            print('period:',start + " - " + end)
            labels.append(start)
            self.backtest(start,end,False,False)
            profits.append(self.realizible_profit)
        this_dir = self.dir +"algorithm2" + "/"
        sum_profit = [profits[0]]
        for i in range(1,len(profits)):
            sum_profit.append(sum_profit[-1] + profits[i])

        try:
            os.mkdir(this_dir)
        except:
            pass
        samplenum = len(labels)
        fig = plt.figure()
        ax = plt.gca()
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        ax.spines['left'].set_position(('data', 0))
        plt.plot(list(range(samplenum)),profits,label = '每日收益曲线')
        plt.plot(list(range(samplenum)),sum_profit,label = "累积收益曲线")
        plt.legend(loc = 'upper right')
        plt.xlabel("day")
        plt.ylabel("number")
        plt.title("100日收益曲线")
        plt.savefig(this_dir + "profit_curve_{}.png".format(self.param_suffix_str))
    def plot(self):
        pass
    def exit_f2(self):
        self.predict = self.predict[:len(self.real)]
        self.winratio.append(self.cal_trend_correct_ratio(self.real,self.predict))
    def exit_f1(self):
        fig = plt.figure(figsize=(12,8))
        plt.plot(self.real,label = "真实的变化")
        plt.plot(self.preditct,label = "预测的变化")
        plt.title("用10点-12点的数据喂模型")
        plt.legend(loc = "upper_left")
        suffix = ""
        for key in self.param:
            suffix += str(key) +"="+str(self.param[key]) + "&"
        g = lambda x: 1 if x > 0 else -1
        f = lambda x,y: 1 if x == y else 0
        trend_real = [g(x) for x in self.real]
        trend_predic = [g(x) for x in self.preditct]
        ratio = sum([f(trend_real[i],trend_predic[i]) for i in range(len(trend_predic))])/(len(trend_predic))
        suffix += "趋势正确预测率_"+str(round(ratio,2))
        plt.savefig(self.dir + "10点-12点数据训练模型_"+suffix + ".png")
    def cal_trend_correct_ratio(self,real,predict):
        g = lambda x: 1 if x > 0 else -1
        f = lambda x, y: 1 if x == y else 0
        trend_real = [g(x) for x in real]
        trend_predic = [g(x) for x in predict]
        if len(trend_real) == 0:
            return np.nan
        ratio = sum([f(trend_real[i], trend_predic[i]) for i in range(len(trend_predic))]) / (len(trend_predic))
        return round(ratio,2)
    def algorithm1(self):
        '''用早上10点-12点的数据喂HMM'''
        self.param['n'] = 10
        self.param['obeserve'] = 6
        self.param['threhold'] = 70
        LastDay = ""
        STATE = 'IDLE'
        X = []
        History = exchange.GetRecords(PERIOD_M1)
        lastticker = History[-2]
        lts = lastticker.Time / 1000
        train_model = False
        self.accumulate_profit = 0
        self.real = []
        self.predict = []
        self.total_ratio = []
        COMPARE = False
        self.profits = []
        NeedStop = False
        self.stop = {
            "LONG":[],
            "SHORT":[],
        }
        hastart = False

        while True:
            ticker = exchange.GetTicker()
            #优先止损 亏损保持在5美元以内
            self.stop["LONG"] = list(sorted(self.stop["LONG"],key = lambda x:x[0]))
            self.stop["SHORT"] = list(sorted(self.stop["SHORT"], key=lambda x: x[0],reverse=True))
            for item in self.stop["LONG"]:
                if ticker.Buy * 0.9999 - item[0] >= -1*item[1] * 5 / 0.1:
                    exchange.Sell(ticker.Buy * 0.9999, 1 * item[1])
                    self.stop["LONG"].remove(item)
            for item in self.stop["SHORT"]:
                if item[0] - ticker.Sell * 1.0001 >= -1*item[1] * 5 / 0.1:
                    exchange.Buy(ticker.Sell * 1.0001, 1 * item[1])
                    self.stop["SHORT"].remove(item)
            tickertime = strategy.ticktime(ticker)
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                Log("进入新的一天")
                dts = ticker.Time / 1000
                LastDay = NowDay
                train_model = False
                O = []

            if ticker.Time/1000 - dts >= 36000 and ticker.Time/1000 - dts < 43200:
                "十点至十二点的数据喂养模型"
                change = ticker.Last - lastticker.Last
                X.append([change])
            else:
                if not hastart:
                    last_check_ticker = ticker
                    hastart = True
            if ticker.Time/1000 - dts >= 43200 and ticker.Time/1000 - dts < 64800:
                if ticker.Time/1000 - last_check_ticker.Time/1000 <  self.param['gap']*60:
                    #需要跳过
                     continue
                lastticker = last_check_ticker
                change = ticker.Last - lastticker.Last
                O.append([change])
                "十二点到下午六点进行交易"
                if COMPARE:
                    self.real.append(change)
                    #print("预测:", self.predict[-1], " 实际:", change,end = " ")
                    #print("当前成交价:",ticker.Last ," 上一时刻成交价:",lastticker.Last)
                    #print("买一:",ticker.Buy," 卖一:",ticker.Sell,end=" ")
                    if STATE == 'LONG':
                        print("买: ",price)
                        if  price - ticker.Buy * 0.9999 >= self.param['p'] * 30 / 0.1 :
                            print("变动过大,止损,有仓位需要后续止损")
                            self.stop[STATE].append((price,self.param['p']))
                        else:
                            exchange.Sell(ticker.Buy * 0.9999, 1 * self.param['p'])
                            print("收益:",ticker.Buy * 0.9999 - price)
                            self.profits.append(ticker.Buy * 0.9999 - price)
                        STATE = "IDLE"

                    if STATE == 'SHORT':
                        print("卖: ", price)
                        if  ticker.Sell * 1.0001 - price>= self.param['p'] * 30 / 0.1 :
                            print("变动过大,止损,有仓位需要后续止损")
                            self.stop[STATE].append((price,self.param['p']))
                        else:
                            exchange.Buy(ticker.Sell * 1.0001, 1 * self.param['p'])
                            print("收益:",price - ticker.Sell * 1.000 )
                            self.profits.append(price - ticker.Sell * 1.000)
                        STATE = "IDLE"
                    COMPARE = False
                    #print()
                if not train_model:
                    "先训练模型"
                    m = hmm.GaussianHMM(n_components=self.param['n'],covariance_type="full")
                    seen = np.array(X).reshape(-1, 1)
                    try:
                        m.fit(seen)
                    except:
                        return 0
                    train_model = True
                    trans = m.transmat_
                else:
                    "训练好模型,观察到5个就交易,就对下一个进行交易"
                    if len(O) == self.param['obeserve'] and len(self.stop["LONG"]) + len(self.stop["SHORT"]) <= 2:
                        "最多只能有两个未止损"
                        try:
                            I = m.predict_proba(O)
                        except:
                            return 0
                        TRAN = I[-1:]
                        next_state_pro = (TRAN @ trans).T
                        distriution_means = m.means_
                        expected_change = (next_state_pro.T @ distriution_means)[0][0]
                        if expected_change > self.param['threhold'] and STATE == "IDLE":
                            exchange.Buy(ticker.Sell *1.0001, 1 * self.param['p'])
                            STATE = "LONG"
                            price = ticker.Sell *1.0001
                        if expected_change < -1*self.param['threhold'] and STATE == "IDLE":
                            exchange.Sell(ticker.Buy *0.9999, 1 * self.param['p'])
                            STATE = "SHORT"
                            price = ticker.Buy *0.9999
                        self.predict.append(expected_change)
                        COMPARE = True
                        O = O[1::]
                        #O = []
                last_check_ticker = ticker
            if ticker.Time/1000 - dts >= 86250:
                Log("进入一天末尾准备平仓")
                for item in self.stop["LONG"]:
                    exchange.Sell(ticker.Buy * 0.9999, 1 * item[1])
                    self.stop["LONG"].remove(item)
                for item in self.stop["SHORT"]:
                    exchange.Buy(ticker.Sell * 1.0001, 1 * item[1])
                    self.stop["SHORT"].remove(item)
                STATE = 'IDLE'
                Log(exchange.GetAccount())
                print(self.profits)
                print(sum(self.profits))
            lastticker = ticker

    def algorithm2(self):
        '''用早上10点-12点的数据喂HMM'''
        self.param['n'] = 18
        self.param['obeserve'] = 5
        self.param['threhold'] = 20
        self.param['stop'] = True
        LastDay = ""
        STATE = 'IDLE'
        X = []
        History = exchange.GetRecords(PERIOD_M1)
        lastticker = History[-2]
        lts = lastticker.Time / 1000
        train_model = False
        self.accumulate_profit = 0
        self.real = []
        self.predict = []
        self.total_ratio = []
        COMPARE = False
        self.profits = []
        NeedStop = False
        self.stop = {
            "LONG": [],
            "SHORT": [],
        }
        hastart = False
        hastrainstart = False
        while True:
            ticker = exchange.GetTicker()
            # 优先止损 亏损保持在5美元以内
            '''
            self.stop["LONG"] = list(sorted(self.stop["LONG"], key=lambda x: x[0]))
            self.stop["SHORT"] = list(sorted(self.stop["SHORT"], key=lambda x: x[0], reverse=True))
            for item in self.stop["LONG"]:
                if ticker.Buy * 0.9999 - item[0] >= -1 * item[1] * 5 / 0.1:
                    exchange.Sell(ticker.Buy * 0.9999, 1 * item[1])
                    self.stop["LONG"].remove(item)
            for item in self.stop["SHORT"]:
                if item[0] - ticker.Sell * 1.0001 >= -1 * item[1] * 5 / 0.1:
                    exchange.Buy(ticker.Sell * 1.0001, 1 * item[1])
                    self.stop["SHORT"].remove(item)
            '''
            tickertime = strategy.ticktime(ticker)
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                Log("进入新的一天")
                dts = ticker.Time / 1000
                LastDay = NowDay
                train_model = False
                O = []

            if ticker.Time / 1000 - dts >= 25000 and ticker.Time / 1000 - dts < 43200:
                "十点至十二点的数据喂养模型"
                if not hastrainstart:
                    last_train_ticker = lastticker
                    hastrainstart = False
                if ticker.Time / 1000 - last_train_ticker.Time / 1000 < self.param['gap'] * 60:
                    # 需要跳过
                    continue
                change = ticker.Last - last_train_ticker.Last
                X.append([change])
                last_train_ticker = ticker
            else:
                if not hastart:
                    last_check_ticker = ticker
                    hastart = True
            if ticker.Time / 1000 - dts >= 43200 and ticker.Time / 1000 - dts < 64800:
                if ticker.Time / 1000 - last_check_ticker.Time / 1000 < self.param['gap'] * 60:
                    # 需要跳过
                    continue
                lastticker = last_check_ticker
                change = ticker.Last - lastticker.Last
                O.append([change])
                "十二点到下午六点进行交易"
                if COMPARE:
                    self.real.append(change)
                    #print("预测:", self.predict[-1], " 实际:", change,end = " ")
                    #print("当前成交价:",ticker.Last ," 上一时刻成交价:",lastticker.Last)
                    #print("买一:",ticker.Buy," 卖一:",ticker.Sell,end=" ")
                    if STATE == 'LONG':
                            print("买: ",price)
                            exchange.Sell(ticker.Buy * 0.9999, 1 * self.param['p'])
                            print("收益:",ticker.Buy * 0.9999 - price)
                            self.profits.append(ticker.Buy * 0.9999 - price)
                            STATE = "IDLE"

                    if STATE == 'SHORT':
                            print("卖: ", price)
                            exchange.Buy(ticker.Sell * 1.0001, 1 * self.param['p'])
                            print("收益:",price - ticker.Sell * 1.000 )
                            self.profits.append(price - ticker.Sell * 1.000)
                            STATE = "IDLE"
                    COMPARE = False

                if not train_model:
                    "先训练模型"
                    m = hmm.GaussianHMM(n_components=self.param['n'], covariance_type="full")
                    seen = np.array(X).reshape(-1, 1)
                    try:
                        m.fit(seen)
                    except:
                        return 0
                    train_model = True
                    trans = m.transmat_
                else:
                    "训练好模型,观察到5个就交易,就对下一个进行交易"
                    if len(O) == self.param['obeserve'] :
                        "最多只能有两个未止损"
                        try:
                            I = m.predict_proba(O)
                        except:
                            return 0
                        TRAN = I[-1:]
                        next_state_pro = (TRAN @ trans).T
                        distriution_means = m.means_
                        expected_change = (next_state_pro.T @ distriution_means)[0][0]
                        if expected_change > self.param['threhold'] and STATE == "IDLE":
                                exchange.Buy(ticker.Sell * 1.0001, 1 * self.param['p'])
                                STATE = "LONG"
                                price = ticker.Sell * 1.0001

                        if expected_change < -1 * self.param['threhold'] and STATE == "IDLE":
                                ''
                                exchange.Sell(ticker.Buy * 0.9999, 1 * self.param['p'])
                                STATE = "SHORT"
                                price = ticker.Buy * 0.9999

                        self.predict.append(expected_change)
                        COMPARE = True
                        O = O[1::]
                        # O = []
                last_check_ticker = ticker
            if ticker.Time / 1000 - dts >= 86250:
                Log("进入一天末尾准备平仓")
                for item in self.stop["LONG"]:
                    exchange.Sell(ticker.Buy * 0.9999, 1 * item[1])
                    self.stop["LONG"].remove(item)
                for item in self.stop["SHORT"]:
                    exchange.Buy(ticker.Sell * 1.0001, 1 * item[1])
                    self.stop["SHORT"].remove(item)
                STATE = 'IDLE'
                Log(exchange.GetAccount())
                print(self.profits)
                print(sum(self.profits))
            lastticker = ticker

    def RSI(self):
        LastDay = ""
        History = exchange.GetRecords(PERIOD_M1)
        lastticker = History[-2]
        self.real = []
        self.metrics = []
        self.stop = {
            "LONG": [],
            "SHORT": [],
        }
        self.param['metrics'] = 'RSI'
        while True:
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                #Log("进入新的一天")
                dts = ticker.Time / 1000
                LastDay = NowDay
            if ticker.Time / 1000 - dts >= 36000 and ticker.Time / 1000 - dts < 57600:
                "十点至下午四点的数据观察指标与真实变动的情况"
                change = ticker.Last
                self.real.append(change)
                records = exchange.GetRecords(PERIOD_M1)[:-2][::-1];
                rsi = TA.RSI(records)
                self.metrics.append(rsi[-1])
            lastticker = ticker
    def OBV(self):
        LastDay = ""
        History = exchange.GetRecords(PERIOD_M1)
        lastticker = History[-2]
        self.real = []
        self.metrics = []
        self.stop = {
            "LONG": [],
            "SHORT": [],
        }
        self.param['metrics'] = 'OBV'
        while True:
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                # Log("进入新的一天")
                dts = ticker.Time / 1000
                LastDay = NowDay
            if ticker.Time / 1000 - dts >= 36000 and ticker.Time / 1000 - dts < 57600:
                "十点至下午四点的数据观察指标与真实变动的情况"
                change = ticker.Last
                self.real.append(change)
                records = exchange.GetRecords(PERIOD_M1)[:-2][::-1];
                OBV = TA.OBV(records)
                self.metrics.append(OBV[-1])
            lastticker = ticker
    def MACD(self):
        LastDay = ""
        History = exchange.GetRecords(PERIOD_M1)
        self.real = []
        self.metrics = []
        self.stop = {
            "LONG": [],
            "SHORT": [],
        }
        self.param['metrics'] = 'MACD'
        while True:
            ticker = exchange.GetTicker()
            NowDay = get_day(ticker.Time)
            if NowDay != LastDay:
                # Log("进入新的一天")
                dts = ticker.Time / 1000
                LastDay = NowDay
            if ticker.Time / 1000 - dts >= 36000 and ticker.Time / 1000 - dts < 57600:
                "十点至下午四点的数据观察指标与真实变动的情况"
                change = ticker.Last-lastticker.Last
                #change = ticker.Last
                self.real.append(change)
                records = exchange.GetRecords(PERIOD_M1)[:-2][::-1];
                MACD = TA.MACD(records, 40, 80, 20)
                self.metrics.append([MACD[0][-1],MACD[1][-1],MACD[2][-1]])
            lastticker = ticker
    def GET_SAR(self,history:list,period:int = 4):
        '''传入一个历史K线数据,计算对应的SAR序列'''
        SAR = np.zeros_like(history)
        states = np.zeros_like(history)
        SAR[:period - 1] = None
        #首先确定第一天是涨势还是跌势

        for i in range(period - 1,len(history) - 1):
            if i == period - 1 or states[i - 1] == 'reserve':
                #设置跳转后进入新阶段的SAR值
                if (history[i].Close > history[period - 1].Open and i == period - 1) or (states[i] == 'long' and states[i-1] == 'reserve'):
                    states[i] = 'long'
                    SAR[i] = min(map(lambda x: x.Low, history[:period]))#该周期内的最小值
                    EP = max(map(lambda x: x.High, history[:period]))#该周期类的最大值
                    AF = 0.02
                if (history[i].Close <= history[period - 1].Open and i == period - 1) or (states[i] == 'short' and states[i-1] == 'reserve'):
                    states[i] = 'short'
                    SAR[i] = max(map(lambda x: x.High, history[:period]))#该周期内的最大值
                    EP = min(map(lambda x: x.Low, history[:period]))#该周期类的最小值
                    AF = 0.02
            else:
                SAR[i] = SAR[i - 1] + AF*(EP - SAR[i - 1])
                if states[i -1] == 'long':
                    if SAR[i] > history[i].Low:
                        states[i] = 'reserve'
                        states[i+1] = 'short'
                    else:
                        states[i] = 'long'
                        EP = max(map(lambda x: x.High, history[i+1-period:i+1]))#该周期类的最大值
                        if history[i].High > max(map(lambda x: x.High, history[i-period:i])):
                            #如果该时间段的最低价L（t+1），比前面N个时间段（即，t-N+1，……，t）的最低价低
                            AF = min(AF + 0.02,0.2)
                if states[i - 1] == 'short':
                    if SAR[i] < history[i].High:
                        states[i] = 'reserve'
                        states[i+1] = 'long'
                    else:
                        states[i] = 'short'
                        EP = min(map(lambda x: x.Low, history[i+1-period:i+1]))#该周期类的最小值
                        if history[i].Low < min(map(lambda x: x.Low, history[i-period:i])):
                            #如果该时间段的最低价L（t+1），比前面N个时间段（即，t-N+1，……，t）的最低价低
                            AF = min(AF + 0.02,0.2)
        return (SAR,states)
    def draw_SAR(self):
        LastDay = ""
        History = exchange.GetRecords(PERIOD_M1) ##股票数据，格式是往列表里添加元组, 每个元组代表一个股票信息。其中元组的格式是（日期，开盘价，最高价，最低价，收盘价）
        datalist = list(map(lambda x:[float(x.Time/1000),x.Open,x.High,x.Low,x.Close],History[:-1]))
        last = list(map(lambda x:x.Open,History[:-1]))
        self.GET_SAR(History,self.period)
        thisdir = self.dir +"SAR" + "/"
        try:
            os.mkdir(self.dir)
        except:
            pass
        fig = plt.figure(figsize=(15,8))
        #datalist= [(date2num(parse(str(20181110))),10,20,5,15)]
        ax = plt.gca()
        #ax.xaxis.set_ticks_position('bottom')
        #ax.yaxis.set_ticks_position('left')  # 指定下边的边作为 x 轴   指定左边的边为 y 轴
        #ax.spines['bottom'].set_position(('data', 0))  # 指定 data  设置的bottom(也就是指定的x轴)绑定到y轴的0这个点上
        #ax.spines['left'].set_position(('data', 0))
        #mpf.candlestick_ohlc(ax, datalist, width=11, colorup='r', colordown='b', alpha=1)  ##设置利用mpf画股票K线图
        ax.set_ylabel("k线")
        ax.set_xlabel("样本")
        (SAR,states) = self.GET_SAR(History,self.period)
        ax.plot(last,linewidth = 1,color = 'red',label = '分钟k线价格')
        for i in range(self.period - 1, len(last)):
            color = {"long": 'orange', "short": "green", "reserve": 'black'}[states[i]]
            marker = 'o' if states[i] != 'reserve' else 'x'
            size = 50 if states[i] == 'reserve' else 9
            ax.scatter(i, SAR[i], s=size, color=color, marker=marker)
        plt.title(self.title)
        plt.legend(loc = 'upper right')
        plt.savefig(thisdir + "8月10日前{}条1分钟k线数据_".format(len(last))+str(self.title) + ".png")
    def main(self):
        self.algorithm2()
a = HMM()
a.testall()

'''
for period in [3,4,5,10,15,20,30,40,50]:
    a.period = period
    a.title = 'SAR周期'+str(a.period) + '_1分钟k线价格与1分钟K线所求SAR值_黑_跳转_紫_涨势_绿_跌势'
    a.backtest('2019-07-08','2019-07-09')
'''
'''
a.param['metrics'] = 'OBV'
a.param['title'] = '30日成交价与' + a.param['metrics'] + '值曲线'
a.testmetric()
'''

'''
for period in [5]:
    a.param['metrics'] = 'RSI'
    a.param['metrics_period'] = period
    a.param['title'] = '五日成交价值与'+a.param['metrics']+ '值曲线'
    a.testmetric()
'''