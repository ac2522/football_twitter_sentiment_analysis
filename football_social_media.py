import requests
import pandas as pd
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

list_ = ["https://twitter.com/GoalProfits/lists/english-championship/members",
         "https://twitter.com/premierleague/lists/premier-league-clubs/members?lang=en",
         "https://twitter.com/GoalProfits/lists/german-bundesliga",
         "https://twitter.com/GoalProfits/lists/german-2-bundesliga",
         "https://twitter.com/GoalProfits/lists/brazilian-serie-a/members",
         "https://twitter.com/GoalProfits/lists/french-ligue-1/members",
         "https://twitter.com/GoalProfits/lists/spanish-primera/members",
         "https://twitter.com/GoalProfits/lists/italian-serie-a/members",
         "https://twitter.com/GoalProfits/lists/scottish-premiership/members",
         "https://twitter.com/GoalProfits/lists/dutch-eredivisie/members",
         "https://twitter.com/GoalProfits/lists/north-american-mls/members",
         "https://twitter.com/GoalProfits/lists/norwegian-tippeligaen/members",
         "https://twitter.com/GoalProfits/lists/swedish-allsvenskan/members",
         "https://twitter.com/GoalProfits/lists/irish-premier/members"]
# can increase data set, but I am lazy so these are all


csv_list = ['E1 (1).csv', 'E0 (1).csv', 'E1.csv', 'N1 (1).csv', 'F1 (1).csv', 'F1 (2).csv', 'N1 (2).csv',
            'N1.csv', 'F1.csv', 'SP1.csv', 'SP1 (1).csv', 'SP1 (2).csv', 'SC0 (2).csv', 'SC0.csv',
            'SC0 (1).csv', 'D1 (2).csv', 'D2 (2).csv', 'D2 (1).csv', 'D1 (1).csv', 'D2.csv', 'E1 (2).csv',
            'D1.csv', 'E0 (2).csv']
# from http://www.football-data.co.uk/data.php  I didn't automate this as this is not a good data source
# there are a lot of stats missing and if you looked you can probably find better sources


def fuzz_comp(string):
    best_score = 0
    for i in twitter_stats:
        if (i in string) or (string in i):
            return(twitter_stats[i])
        similarity = fuzz.token_sort_ratio(string, i)
        if similarity > best_score:
            best_score = similarity
            best_ = twitter_stats[i]
        if best_score < 0.6:
            return 0
    return best_


def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')


def twitter_data(list_):
    handles = {}
    for twitter_page in list_:
        result = requests.get(twitter_page)
        src = result.content
        soup = BeautifulSoup(src, 'html.parser')
        members = soup.find_all('div', {'class': "activity-user-profile-content"})
        for i in members:
            name = i.find(class_="fullname").text
            handle = i.find(class_="username u-dir u-textTruncate").text
            handles[deEmojify(name)] = handle

    twitter_stats = handles.copy()
    style_ = "font-size: 1.6em; color: #41a200; padding-top: 10px; font-weight: 600; margin-top: -15px;"
    for handle in handles.keys():
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        url = "https://socialblade.com/twitter/user/" + handles[handle][1:]
        src = requests.get(url, headers=headers).text

        soup = BeautifulSoup(src, 'html.parser')
        atv = soup.find('div', {'class': "YouTubeUserTopInfo"})
        followers = atv.text.split()[1].replace(',', '')
        try:
            stats = soup.findAll("p", {"style": style_})
            retweets = stats[1].text.replace(',', '')
            likes = stats[2].text.replace(',', '')
        except:
            likes = retweets = 0
        print(handle + ":", followers, retweets, likes)
        if 'Football Club' in handle:
            twitter_stats[handle.split()[0]] = [followers, retweets, likes]
            del twitter_stats[handle]
        else:
            twitter_stats[handle] = [followers, retweets, likes]
    return twitter_stats


def football_data(csv_list):
    # df = pd.read_csv("http://www.football-data.co.uk/mmz4281/1617/E0.csv") and download all directly from website
    df = pd.read_csv('E0.csv')
    for i in csv_list:
        try:
            df.append(pd.read_csv(i))
        except UnicodeDecodeError:
            continue
    df.rename(columns={'AwayTeam': 'team1', 'HomeTeam': 'team0'})
    return df


def implement_stats(df, twitter_stats):
    df['statsh'] = [fuzz_comp(w) for w in df.team0]
    df = df[df.statsh != 0]
    df['statsa'] = [fuzz_comp(w) for w in df.team1]
    df = df[df.statsa != 0]

    df['stat1'] = [w[0] for w in df.statsh]
    df['stat2'] = [w[1] for w in df.statsh]
    df['stat3'] = [w[2] for w in df.statsh]

    df['stat_1'] = [w[0] for w in df.statsa]
    df['stat_2'] = [w[1] for w in df.statsa]
    df['stat_3'] = [w[2] for w in df.statsa]
    return df


def cleaning_data(df):
    df1 = df[['FTR', 'stat1', 'stat2', 'stat3', 'B365H', 'Date', 'stat_1', 'stat_2', 'stat_3']].copy()
    df1.rename(columns={'FTR': 'result', 'B365H': 'odds', 'Date': 'date',
                        'stat1': 'h1', 'stat2': 'h2', 'stat3': 'h3',
                        'stat_1': 'a1', 'stat_2': 'a2', 'stat_3': 'a3'}, inplace=True)
    df1['location'] = 0
    df1['result'] = [int(w) for w in df1['result'] == 'H']
    df2 = df[['FTR', 'stat_1', 'stat_2', 'stat_3', 'B365A', 'Date', 'stat1', 'stat2', 'stat3']].copy()
    df2['location'] = 1
    df2.rename(columns={'FTR': 'result',  'B365A': 'odds', 'Date': 'date', 'stat_1': 'h1',
                        'stat_2': 'h2', 'stat_3': 'h3', 'stat1': 'a1', 'stat2': 'a2', 'stat3': 'a3'}, inplace=True)
    df2['result'] = [int(w) for w in df2['result'] == 'A']
    dataset = pd.concat([df1, df2])
    dataset['odds2'] = 1 / dataset['odds']
    dataset['date'] = [2019 - int(w.split("/")[2]) for w in dataset.date]
    dataset.reset_index(inplace=True)
    dataset.drop(['index'], axis=1, inplace=True)
    return dataset


def cleaning_data2(df):  # Could combine this w/ above but it might be a little messy

    df1 = df[['team0', 'stat1', 'stat2', 'stat3', 'odds0', 'date', 'stat_1', 'stat_2', 'stat_3', 'location']].copy()
    df1.rename(columns={'odds0': 'odds', 'stat1': 'h1', 'stat2': 'h2', 'stat3': 'h3',
                        'team0': 'team', 'stat_1': 'a1', 'stat_2': 'a2', 'stat_3': 'a3'}, inplace=True)
    df2 = df[['team1', 'stat_1', 'stat_2', 'stat_3', 'odds1', 'date', 'stat1', 'stat2', 'stat3']].copy()
    df2['location'] = 1
    df2.rename(columns={'odds1': 'odds', 'stat_1': 'h1', 'stat_2': 'h2', 'stat_3': 'h3',
                        'team1': 'team', 'stat1': 'a1', 'stat2': 'a2', 'stat3': 'a3'}, inplace=True)
    dataset = pd.concat([df1, df2])
    dataset['odds2'] = 1 / dataset['odds']
    dataset.set_index('team', inplace=True)
    return dataset


def machine_learning():
    # havent done yet, I couldn't find a suitable model
    # am thinking that a deep reinforcement learning would work best
    # as you want the result to be the odds multiplied by whether it was a win
    # The lack of variables means that even if I were to get a good model, there would be too much uncertainty
    # too much chaos, so I would need to add other variables such as which players are playing,
    # which would require a larger dataset and a much better gpu

    # adding win streak, mean wins that season would also help
    # converting years to season would be good, but difficult given that different leagues have different season dates
    # adding goal keeper and defence statistics would mean you could analyse the possibility of a draw
    # adding position in league and how far they are from te player above and below
    # a sentiment analysis of the tweets that the teams are being tagged in might also be interesting and fun to make
    # you could even use a sentiment analysis of player tweets to read a players emotions and how distracted they are
    return model


def invest(prediction):  # inputs model predictions
    # how many good value predictions are there and how much to put in each
    return prediction  # outputs panda series team name and value to invest


# could scan oddschecker to get best odds, but qould require man many betting accounts
# plus smarkets tends to have best odds along with betfair (except smarkets takes only 2% comission compared to 5%)
# I have to use selenium as have had some forbidden access errors with beautifulsoup
class smarkets_bot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.model = model

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome('./chromedriver.exe', chrome_options=chrome_options)

        self.base_url = 'https://smarkets.com/listing/sport/football?period=today'

    def login(self):  # logs into account, this doesnt work if you have 2 factor authentication obviously
        self.driver.get('https://smarkets.com/login')
        self.driver.find_element_by_xpath('//*[@id="login-form-email"]').send_keys(self.username)
        self.driver.find_element_by_xpath('//*[@id="login-form-password"]').send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="smarkets"]/div[3]/div/div/div[1]/form/button').click()

    def buy(self, prediction):  # buys stake in certain games
        self.driver.get(self.base_url)
        for i, e in enumerate(prediction.index):
            xpath_search = """//span[contains(@class, 'contract-name') and text() = '{}']/ancestor::span[
            contains(@class, 'contract-item ') or contains(@class, 'contract-item top')]""".format(e)

            contract_item = self.driver.find_elements_by_xpath(xpath_search)

            contract_item.find(class_="price tick buy   formatted-price numeric-value").click()

            self.driver.find_element_by_xpath("//input[@class='param-text-input text-input numeric-value']"
                                              ).send_keys(prediction.iloc[i])
            self.driver.find_element_by_xpath("//button[@class='confirm-bet-button -accented micro-button']").click()
            self.driver.find_element_by_xpath("//button[@class='confirm-bet-button -accented micro-button']").click()
# the button for confirm bet has same link as the place bet button

    def match_finder(self):  # scans all matches and outputs them ready for predicting
        matches = pd.DataFrame(columns=['team0', 'odds0', 'team1', 'odds1', 'date', 'location'])

        self.driver.get(self.base_url)
        WebDriverWait(self.driver, timeout=10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/main/div[3]')))
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        atv = soup.find_all("div", {"class": "contract-items  open"})  # finds all open matches

        for i, e in enumerate(atv):
            options_ = e.find_all(class_="contract-item")
            options_.append(e.find(class_="contract-item top"))  # most traded team is labeled top
            found = False
            match = {'date': 0, 'location': 0}
            for j, option in enumerate(options_):
                name_ = option.find(class_="contract-name").text
                if name_ == 'Draw':  # we dont want draws
                    found = j
                    continue
                if (j == 0) or (found == 0 and j == 2):
                    loc = 0  # these loops to determine which is home and away
                    found = True
                else:
                    loc = 1
                odds = 1 / option.find(class_="price tick buy   formatted-price numeric-value").text
                match.update({'team{}'.format(loc): name_, 'odds{}'.format(loc): odds})
            matches.loc[i] = match
        matches = cleaning_data2(implement_stats(matches, twitter_stats))
        return matches


if __name__ == '__main__':

    try:
        print(type(model))
    except NameError:
        twitter_stats = twitter_data(list_)
        df = football_data(csv_list)
        df = implement_stats(df, twitter_stats)  # merges twitter stats and data
        df = cleaning_data(df)  # formats data
        model = machine_learning(df)  # creates model
        del df  # clears memory

    todays_findings = smarkets_bot('AlexCar67788266', 'TryBot12', model)

    matches = todays_findings.match_finder()

    prediction = model.predict(matches)
    prediction = invest(prediction)

# todays_findings.login()
# todays_findings.buy(prediction)
