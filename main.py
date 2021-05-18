import cryptocompare
import pprint
from binance.client import Client

ACTUAL_INVESTMENT = float(0)  # Manually count up your actual investment here, binance does not account for fees.

menuDict = dict()

API_KEY = ""  # Your Binance API Key
API_SECRET = ""  # Your Binance API Secret

CRYPTO_COMPARE_API_KEY = ""  # Your cryptocurrency compare api key, found at https://www.cryptocompare.com/

cryptocompare.cryptocompare._set_api_key_parameter(CRYPTO_COMPARE_API_KEY)


def kermit():
    exit()


class CryptoApp:
    def __init__(self):
        self.loaded = False
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.client = Client(self.api_key, self.api_secret)
        self.currentMenu = None
        self.dataDealer = cryptoDataDealer(self)
        self.initMenus()
        self.inputHandler = inputHandler(self)
        self.dataDealer.enable()

    def getClient(self):
        return self.client

    def getLoaded(self):
        return self.loaded

    def getInputHandler(self):
        return self.inputHandler

    def getDataDealer(self):
        return self.dataDealer

    def getEarliestTimestamp(self):
        return enumerate(self.getClient().get_my_trades())

    def getCurrentMenu(self):
        return self.currentMenu

    def getTotalSpentInvestment(self):
        # trades = self.getClient().get_all_orders(symbol='GBPBUSD')
        # THIS DOES NOT INCLUDE FEES IF YOU ORIGINALLY USED CARD
        # totalGBP = 0
        # for entry in trades:
        #     qty = float(entry['origQty'])
        #     totalGBP += qty
        return ACTUAL_INVESTMENT

    def destroy(self):
        if not self.getLoaded():
            return
        exit()

    def initMenus(self):
        firstPanel = menuPanel('Main Menu', 1,
                               sections={'See Total investment': self.getTotalSpentInvestment(),  # see total spent
                                         'Get Asset Breakdown & Value': self.getDataDealer().accountSnapshot(),  # full account overview
                                         "Current Profit / Loss": self.getDataDealer().getProfitLoss(),
                                         "See 'good' and 'bad' investments": self.getDataDealer().getPriceOverview(),
                                         'Exit': self.destroy()})
        self.currentMenu = firstPanel


class cryptoDataDealer:
    def __init__(self, applet):
        self.loaded = False
        self.applet = applet

    def enable(self):
        self.loaded = True

    def notEnabled(self):
        return self.loaded is True

    def getApplet(self):
        return self.applet

    def getTotalWorth(self):
        info = self.getApplet().getClient().get_account()
        totalGBPWorth = 0
        base = info['balances']
        for balanceSet in base:
            coin = balanceSet['asset']
            value = balanceSet['free']
            if float(value) > 0:
                gbpValue = self.getActualWorth(coin, float(value))
                totalGBPWorth += gbpValue
        return round(totalGBPWorth, 2)

    def getProfitLoss(self):
        worth = self.getTotalWorth()
        investment = ACTUAL_INVESTMENT
        profitLoss = float(worth) - float(investment)
        string = '---\n'
        string += Colors.OKGREEN + "Profit " + ":£" + str(profitLoss) + "\n"
        string += '---'
        return string

    def getTotalGBPPaidForPair(self, coin):
        if coin == 'BUSD':
            symbolString = 'GBP' + 'BUSD'
        else:
            symbolString = coin + "BUSD"
        trades = self.getApplet().getClient().get_all_orders(symbol=symbolString, limit=500)
        tradeDict = {coin: 0}
        for item in trades:
            if item['status'] == "FILLED":
                BUSDCost = float(item['cummulativeQuoteQty'])
                tradeDict[coin] = tradeDict[coin] + BUSDCost
        GBPCost = self.getActualWorth('BUSD', tradeDict[coin])
        tradeDict = None
        return float(GBPCost)

    def getOwnedCoinPairsAndValue(self):
        info = self.getApplet().getClient().get_account()
        ownedPairs = {}
        base = info['balances']
        for balanceSet in base:
            coin = balanceSet['asset']
            value = balanceSet['free']
            if float(value) > 0:
                ownedPairs[coin] = value
        return ownedPairs

    def getOwnedCoinPairs(self):
        return self.getOwnedCoinPairsAndValue().keys()

    def accountSnapshot(self):
        totalGBPWorth = 0
        reportData = self.getOwnedCoinPairsAndValue()
        displayData = {}
        worthData = {}
        for coin, value in reportData.items():
            gbpValue = self.getActualWorth(coin, float(value))
            totalGBPWorth += gbpValue
            displayData[coin] = value + " (£" + str(gbpValue) + ")"
            worthData[coin] = self.getActualWorth(coin, float(value))
        baseString = "-------\n"
        baseString += "Current Portfolio spread\n"
        baseString += '-------\n'
        for key, val in displayData.items():
            baseString += key + " > " + val + "\n"
            paidFor = self.getTotalGBPPaidForPair(key)
            worth = worthData[key]
            profitLoss = worth - paidFor
            baseString += "Total spent in " + key + ": £" + str(self.getTotalGBPPaidForPair(key)) + "\n"
            if key == 'BUSD':
                baseString += "\n"
                continue
            color = Colors.FAIL if profitLoss <= 0 else Colors.OKGREEN
            baseString += color + "Profit: £" + str(profitLoss) + "\n" + Colors.OKCYAN
            baseString += "\n"
        baseString += "--\n"
        baseString += Colors.OKGREEN + "Your Portfolio Is Currently worth £" + str(round(totalGBPWorth, 2)) + "\n"
        baseString += "--" + Colors.OKBLUE
        return baseString

    def getActualWorth(self, coin, value):
        price = cryptocompare.get_price(coin, currency='GBP')[coin]['GBP'] * value
        return float(price)

    def getCurrentPriceForCoin(self, coin):
        if coin == 'BUSD':
            return ''
        priceDict = self.getApplet().getClient().get_symbol_ticker(symbol=coin + 'BUSD')
        currentPrice = priceDict['price']
        return round(float(currentPrice), 5)

    def getAveragePurchasePriceForCoin(self, coin):
        if coin == 'BUSD':
            return ''
        orders = self.getApplet().getClient().get_all_orders(symbol=coin + 'BUSD')
        totalValuePurchased = float(0)
        totalOrderCount = 0
        for order in orders:
            if order['status'] == 'FILLED':
                totalOrderCount = totalOrderCount + 1
                totalValuePurchased += float(order['price'])
        averagePrice = totalValuePurchased / totalOrderCount
        averagePrice = round(averagePrice, 5)
        return averagePrice

    def getPriceOverview(self):
        coinPairs = self.getOwnedCoinPairs()
        baseString = "----------\n"
        baseString += Colors.BOLD + "Asset Pricing Overview\n"
        for coin in coinPairs:
            if coin == 'BUSD':
                continue
            baseString += "--------\n"
            baseString += Colors.OKBLUE + coin + ":\n"
            averageCoinPrice = self.getAveragePurchasePriceForCoin(coin)
            currentCoinPrice = self.getCurrentPriceForCoin(coin)
            color = Colors.OKGREEN if currentCoinPrice > averageCoinPrice else Colors.FAIL
            status = color + "PLUS" if currentCoinPrice > averageCoinPrice else color + "DOWN"
            baseString += Colors.ENDC + "Current coin price: $" + Colors.OKCYAN + str(currentCoinPrice) + "\n"
            baseString += Colors.ENDC + "My Average coin purchase price: $" + color + str(averageCoinPrice) + "\n"
            difference = round(currentCoinPrice - averageCoinPrice, 5)
            baseString += Colors.ENDC + "(liquid) Difference is " + color + " $" + str(difference) + "\n"
            baseString += status + "\n" + Colors.ENDC
        return baseString


class inputHandler:
    def __init__(self, application):
        self.app = application

    def getApp(self):
        return self.app

    def getCurrentMenu(self):
        return self.getApp().getCurrentMenu()

    def handleInputCycle(self):
        menu = self.getCurrentMenu()
        if menu is None:
            print("No Menu Found")
        self.getCurrentMenu().printOptions()
        selectionInput = input()
        selectionInput = int(selectionInput)
        if self.isCorrectInput(selectionInput):
            menu = self.getCurrentMenu()
            menu.returnActionFromSelection(selectionInput)
            print("Press any button to continue")
            the = input()
            if str(the) != 'break':
                self.handleInputCycle()
        else:
            print("error: wrong selection, try again.")
            self.handleInputCycle()

    def isCorrectInput(self, input):
        return 0 < input <= self.getCurrentMenu().getMaxAmountOfOptions()


class menuPanel:
    def __init__(self, header, menuID, **options):
        self.id = menuID
        self.header = header
        self.inputPairs = {}
        self.setOptions(options)

    def getMaxAmountOfOptions(self):
        return len(self.inputPairs)

    def getPanelID(self):
        return self.id

    def getHeader(self):
        return self.header

    def setOptions(self, options):
        list = options['sections']
        for item in list:
            self.inputPairs[item] = list[item]

    def printOptions(self):
        print("---")
        print(self.header)
        print("Select an option")
        count = 1
        for key, value in self.inputPairs.items():
            print(str(count) + " " + key)
            count += 1
        print("----")

    def returnActionFromSelection(self, input):
        values = self.inputPairs.values()
        length = len(values)
        if input == length:
            kermit()
        count = 1
        for val in values:
            if count == input:
                if isinstance(val, str) or isinstance(val, float):
                    print(val)
                else:
                    print(val)
            count += 1


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


app = CryptoApp()
app.getInputHandler().handleInputCycle()
